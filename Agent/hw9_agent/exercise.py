from __future__ import annotations

import json
import re
from dataclasses import dataclass
from enum import Enum
from pathlib import Path

from .client import DeepSeekChatClient


PLACEHOLDER_RE = re.compile(r"\{\{([A-Z0-9_]+)\}\}")


class StructuralDiagnosticCode(str, Enum):
    """Deterministic structural-feedback codes exposed to students."""

    UNFILLED_BLANKS = "UNFILLED_BLANKS"
    FRAMEWORK_CHANGED = "FRAMEWORK_CHANGED"
    EMPTY = "EMPTY"
    STRUCTURE_OK = "STRUCTURE_OK"


def _literal_pattern(text: str) -> str:
    """Match fixed template syntax while accepting formatting-only changes."""
    return "".join(
        r"\s+" if part.isspace() else re.escape(part)
        for part in re.split(r"(\s+)", text)
        if part
    )


@dataclass
class ExerciseBundle:
    directory: Path
    config: dict
    requirement: str
    template: str

    @classmethod
    def load(cls, directory: Path) -> "ExerciseBundle":
        config = json.loads((directory / "exercise.json").read_text(encoding="utf-8"))
        # Newly published packages do not need a hand-maintained sample list:
        # every Java file placed under samples/ is a public example.
        if "samples" not in config:
            config["samples"] = _discover_samples(directory / "samples")
        return cls(
            directory=directory,
            config=config,
            requirement=(directory / "requirement.md").read_text(encoding="utf-8"),
            template=(directory / "template.java").read_text(encoding="utf-8"),
        )


def _discover_samples(samples_dir: Path) -> list[dict[str, str]]:
    if not samples_dir.is_dir():
        return []
    return [
        {
            "id": sample.stem,
            "label": "样例：" + sample.stem.replace("-", " ").replace("_", " "),
            "file": f"samples/{sample.name}",
        }
        for sample in sorted(samples_dir.glob("*.java"))
    ]


def deterministic_check(bundle: ExerciseBundle, submission: str) -> list[dict[str, str]]:
    findings: list[dict[str, str]] = []
    remaining = PLACEHOLDER_RE.findall(submission)
    if remaining:
        findings.append({
            "severity": "error",
            "code": StructuralDiagnosticCode.UNFILLED_BLANKS.value,
            "message": "仍有未填写的空格：" + ", ".join(remaining),
        })
    parts = PLACEHOLDER_RE.split(bundle.template)
    expected_names = parts[1::2]
    if expected_names != bundle.config["placeholders"]:
        raise ValueError("Exercise placeholders do not match its template")
    cursor = 0
    initial = re.match(_literal_pattern(parts[0]), submission)
    framework_matches = initial is not None
    if initial:
        cursor = initial.end()
        for index, _name in enumerate(expected_names):
            next_literal = re.search(_literal_pattern(parts[index * 2 + 2]), submission[cursor:])
            if next_literal is None:
                framework_matches = False
                break
            cursor += next_literal.end()
        framework_matches = framework_matches and cursor == len(submission)
    if not framework_matches:
        findings.append({
            "severity": "error",
            "code": StructuralDiagnosticCode.FRAMEWORK_CHANGED.value,
            "message": "接口签名、JML 行为框架或非填写区被修改。",
        })
    if not submission.strip():
        findings.append({
            "severity": "error",
            "code": StructuralDiagnosticCode.EMPTY.value,
            "message": "提交内容为空。",
        })
    if not findings:
        findings.append({
            "severity": "info",
            "code": StructuralDiagnosticCode.STRUCTURE_OK.value,
            "message": "所有空格均已填写，且预设框架保持完整；仍需进行语义审查。",
        })
    return findings


def build_review_prompt(
    project_root: Path,
    bundle: ExerciseBundle,
    submission: str,
    mode: str,
    history: list[dict[str, str]],
    semantic_result: dict | None = None,
) -> str:
    if mode not in bundle.config["allowed_modes"]:
        raise ValueError(f"Unsupported feedback mode: {mode}")
    instructions = (project_root / "prompts" / "student_reviewer.md").read_text(encoding="utf-8")
    sections = [
        instructions,
        "# Requested feedback mode\n\n" + mode,
        "# Natural-language requirement\n\n" + bundle.requirement,
        "# Supplied exercise template\n\n```java\n" + bundle.template + "\n```",
        "# Public interface symbols\n\n```json\n"
        + json.dumps(bundle.config["allowed_symbols"], ensure_ascii=False, indent=2) + "\n```",
        "# Public feedback contract\n\n```json\n"
        + json.dumps(
            {
                "requested": bundle.config["feedback_contract"][mode],
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n```",
        "# Deterministic pre-check\n\n```json\n"
        + json.dumps(deterministic_check(bundle, submission), ensure_ascii=False, indent=2) + "\n```",
    ]
    if semantic_result is not None:
        sections.append(
            "# Authoritative deterministic semantic diagnostics\n\n```json\n"
            + json.dumps(semantic_result, ensure_ascii=False, indent=2)
            + "\n```"
        )
    if history:
        sections.append("# Previous interaction\n\n```json\n" + json.dumps(history, ensure_ascii=False, indent=2) + "\n```")
    sections.append("# Untrusted student submission\n\n```java\n" + submission + "\n```")
    sections.append("# Response instruction\n\nReturn only one valid JSON object in the required feedback mode.")
    return "\n\n---\n\n".join(sections)


def interactive_session(
    client: DeepSeekChatClient,
    project_root: Path,
    bundle: ExerciseBundle,
    mode: str,
) -> None:
    history: list[dict[str, str]] = []
    print(bundle.requirement)
    print("\nJML 模板：\n")
    print(bundle.template)
    print("输入填写后的完整 Java 接口文件，以单独一行 /submit 提交。命令：/template /requirement /mode hint|review /quit")
    buffer: list[str] = []
    while True:
        try:
            line = input("jml> " if not buffer else "...> ")
        except EOFError:
            print()
            return
        command = line.strip()
        if not buffer and command == "/quit":
            return
        if not buffer and command == "/template":
            print(bundle.template)
            continue
        if not buffer and command == "/requirement":
            print(bundle.requirement)
            continue
        if not buffer and command.startswith("/mode "):
            candidate = command.split(maxsplit=1)[1]
            if candidate in bundle.config["allowed_modes"]:
                mode = candidate
                print(f"反馈模式已切换为 {mode}")
            else:
                print("可用模式：hint, review")
            continue
        if command != "/submit":
            buffer.append(line)
            continue
        submission = "\n".join(buffer).strip()
        buffer.clear()
        prompt = build_review_prompt(project_root, bundle, submission, mode, history)
        response = client.generate(prompt).strip()
        print("\n" + response + "\n")
        history.append({"submission": submission, "feedback": response, "mode": mode})
