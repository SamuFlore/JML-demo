from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path

from .client import DeepSeekChatClient
from .parser import load_hw9_catalog


PLACEHOLDER_RE = re.compile(r"\{\{([A-Z0-9_]+)\}\}")
PROTECTED_SCAFFOLD = (
    "public normal_behavior",
    "assignable users[*]",
    "public exceptional_behavior",
    r"assignable \nothing",
    "signals (UserIdNotFoundException e)",
    "signals (SelfSubscriptionException e)",
    "signals (DuplicateSubscriptionException e)",
)


@dataclass
class ExerciseBundle:
    directory: Path
    config: dict
    requirement: str
    template: str
    rubric: dict

    @classmethod
    def load(cls, directory: Path) -> "ExerciseBundle":
        return cls(
            directory=directory,
            config=json.loads((directory / "exercise.json").read_text(encoding="utf-8")),
            requirement=(directory / "requirement.md").read_text(encoding="utf-8"),
            template=(directory / "template.jml").read_text(encoding="utf-8"),
            rubric=json.loads((directory / "rubric.json").read_text(encoding="utf-8")),
        )


def deterministic_check(bundle: ExerciseBundle, submission: str) -> list[dict[str, str]]:
    findings: list[dict[str, str]] = []
    remaining = PLACEHOLDER_RE.findall(submission)
    if remaining:
        findings.append({
            "severity": "error",
            "code": "UNFILLED_BLANKS",
            "message": "仍有未填写的空格：" + ", ".join(remaining),
        })
    for required in PROTECTED_SCAFFOLD:
        if required not in submission:
            findings.append({
                "severity": "error",
                "code": "FRAMEWORK_CHANGED",
                "message": f"题目预先给定的框架被删除或修改：{required}",
            })
    if submission.count("signals (UserIdNotFoundException e)") != 2:
        findings.append({
            "severity": "error",
            "code": "USER_EXCEPTION_COUNT",
            "message": "框架应保留两个 UserIdNotFoundException 条件，分别处理 id1 和 id2。",
        })
    if not submission.strip():
        findings.append({"severity": "error", "code": "EMPTY", "message": "提交内容为空。"})
    if not findings:
        findings.append({
            "severity": "info",
            "code": "STRUCTURE_OK",
            "message": "所有空格均已填写，且预设框架保持完整；仍需进行语义审查。",
        })
    return findings


def official_method_context(source_root: str, bundle: ExerciseBundle) -> dict:
    matches = [
        method
        for interface in load_hw9_catalog(source_root)
        for method in interface.methods
        if method.interface == bundle.config["interface"]
        and method.name == bundle.config["method"]
    ]
    if len(matches) != 1:
        raise ValueError("Exercise method could not be uniquely grounded in the official interfaces")
    return matches[0].to_dict()


def build_review_prompt(
    project_root: Path,
    source_root: str,
    bundle: ExerciseBundle,
    submission: str,
    mode: str,
    history: list[dict[str, str]],
) -> str:
    if mode not in bundle.config["allowed_modes"]:
        raise ValueError(f"Unsupported feedback mode: {mode}")
    instructions = (project_root / "prompts" / "student_reviewer.md").read_text(encoding="utf-8")
    context = official_method_context(source_root, bundle)
    sections = [
        instructions,
        "# Requested feedback mode\n\n" + mode,
        "# Natural-language requirement\n\n" + bundle.requirement,
        "# Supplied exercise template\n\n```java\n" + bundle.template + "\n```",
        "# Official interface grounding\n\n```json\n"
        + json.dumps(context, ensure_ascii=False, indent=2) + "\n```",
        "# Hidden assessment rubric\n\n```json\n"
        + json.dumps(bundle.rubric, ensure_ascii=False, indent=2) + "\n```",
        "# Deterministic pre-check\n\n```json\n"
        + json.dumps(deterministic_check(bundle, submission), ensure_ascii=False, indent=2) + "\n```",
    ]
    if history:
        sections.append("# Previous interaction\n\n```json\n" + json.dumps(history, ensure_ascii=False, indent=2) + "\n```")
    sections.append("# Student submission\n\n```java\n" + submission + "\n```")
    sections.append("# Response instruction\n\nReturn only the YAML review in the required feedback mode.")
    return "\n\n---\n\n".join(sections)


def interactive_session(
    client: DeepSeekChatClient,
    project_root: Path,
    source_root: str,
    bundle: ExerciseBundle,
    mode: str,
) -> None:
    history: list[dict[str, str]] = []
    print(bundle.requirement)
    print("\nJML 模板：\n")
    print(bundle.template)
    print("输入填写后的完整 JML，以单独一行 /submit 提交。命令：/template /requirement /mode hint|review|solution /quit")
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
                print("可用模式：hint, review, solution")
            continue
        if command != "/submit":
            buffer.append(line)
            continue
        submission = "\n".join(buffer).strip()
        buffer.clear()
        prompt = build_review_prompt(
            project_root, source_root, bundle, submission, mode, history
        )
        response = client.generate(prompt).strip()
        print("\n" + response + "\n")
        history.append({"submission": submission, "feedback": response, "mode": mode})

