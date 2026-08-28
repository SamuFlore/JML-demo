from __future__ import annotations

import json
import re
from pathlib import Path

from .model import InterfaceSpec, MethodSpec


PROFILE_PATH = Path(__file__).resolve().parent.parent / "course_profiles" / "hw9_2026.json"
METHOD_RE = re.compile(
    r"(?P<jml>/\*@.*?(?:@\*/|\*/)|//\s*@[^\n]*)\s*"
    r"public\s+(?P<markers>(?:/\*@.*?@\*/\s*)*)"
    r"(?P<signature>[^;{]+?\s+(?P<name>[A-Za-z_]\w*)\s*\([^;{]*?\)"
    r"(?:\s+throws\s+[^;{]+)?)\s*;",
    re.DOTALL,
)
SINGLE_LINE_METHOD_RE = re.compile(
    r"^\s*(?P<jml>//\s*@[^\n]*)\s*$\n"
    r"\s*public\s+(?P<markers>(?:/\*@.*?@\*/\s*)*)"
    r"(?P<signature>[^;{]+?\s+(?P<name>[A-Za-z_]\w*)\s*\([^;{]*?\)"
    r"(?:\s+throws\s+[^;{]+)?)\s*;",
    re.MULTILINE,
)
DECLARATION_RE = re.compile(
    r"public\s+(?P<markers>(?:/\*@.*?@\*/\s*)*)"
    r"(?P<signature>[^;{]+?\s+(?P<name>[A-Za-z_]\w*)\s*\([^;{]*?\)"
    r"(?:\s+throws\s+[^;{]+)?)\s*;",
    re.DOTALL,
)


def _clean_jml(text: str) -> str:
    text = re.sub(r"^/\*@|@?\*/$", "", text.strip())
    text = re.sub(r"^//\s*@\s?", "", text)
    lines = []
    for line in text.splitlines():
        lines.append(re.sub(r"^\s*@\s?", "", line).rstrip())
    return "\n".join(lines).strip()


def _mask_jml_comments(text: str) -> str:
    """Blank JML comments while preserving line breaks and offsets.

    Bare Java declarations are collected after annotated declarations. Without
    masking, `public normal_behavior` inside a JML block can be mistaken for a
    Java declaration when the released interface uses multiline contracts.
    """
    def blank(match: re.Match[str]) -> str:
        return re.sub(r"[^\n]", " ", match.group(0))

    return re.sub(r"/\*@.*?(?:@\*/|\*/)|//[^\n]*", blank, text, flags=re.DOTALL)


def _clauses(jml: str, keyword: str) -> list[str]:
    """Extract top-level clauses without splitting semicolons in quantifiers."""
    result: list[str] = []
    starts = list(re.finditer(rf"(?:^|\n)\s*{keyword}\b\s*", jml))
    for start in starts:
        index = start.end()
        depth = 0
        while index < len(jml):
            char = jml[index]
            if char in "([{":
                depth += 1
            elif char in ")]}":
                depth = max(0, depth - 1)
            elif char == ";" and depth == 0:
                result.append(re.sub(r"\s+", " ", jml[start.end():index]).strip())
                break
            index += 1
        else:
            # The released HW9 interfaces use an invariant block whose final
            # expression is not followed by a semicolon. An invariant is a
            # block-level declaration, so the remainder of that block is its
            # expression; method clauses remain semicolon-terminated.
            if keyword == "invariant":
                expression = re.sub(r"\s+", " ", jml[start.end():]).strip()
                if expression:
                    result.append(expression)
                    continue
            raise ValueError(f"Unterminated JML {keyword} clause")
    return result


def load_course_profile(path: str | Path | None = None) -> dict:
    profile_path = Path(path) if path else PROFILE_PATH
    return json.loads(profile_path.read_text(encoding="utf-8"))


def parse_interface(path: Path) -> InterfaceSpec:
    text = path.read_text(encoding="utf-8")
    interface_match = re.search(r"public\s+interface\s+(\w+)", text)
    if not interface_match:
        raise ValueError(f"No interface declaration found in {path}")
    result = InterfaceSpec(name=interface_match.group(1), source=str(path))

    for block in re.findall(r"/\*@.*?@\*/", text, re.DOTALL):
        cleaned = _clean_jml(block)
        if " instance model " in f" {cleaned} ":
            result.models.extend(_clauses(cleaned, r"(?:public\s+instance\s+)?model"))
        if re.search(r"(?:^|\n)\s*invariant\s", cleaned):
            result.invariants.extend(_clauses(cleaned, "invariant"))

    matches = list(METHOD_RE.finditer(text)) + list(SINGLE_LINE_METHOD_RE.finditer(text))
    matches.sort(key=lambda item: item.start())
    seen: set[tuple[str, str]] = set()
    for match in matches:
        jml = _clean_jml(match.group("jml"))
        markers = re.findall(r"\b(pure|safe)\b", match.group("markers"))
        method = MethodSpec(
            interface=result.name,
            name=match.group("name"),
            signature=re.sub(r"\s+", " ", match.group("signature")).strip(),
            jml=jml,
            markers=markers,
            requires=_clauses(jml, "requires"),
            assignable=_clauses(jml, "assignable"),
            ensures=_clauses(jml, "ensures"),
            signals=_clauses(jml, "signals"),
            behavior_kinds=re.findall(r"\b(normal_behavior|exceptional_behavior)\b", jml),
        )
        key = (method.name, method.signature)
        if key not in seen:
            result.methods.append(method)
            seen.add(key)
    # A teacher may provide a Java interface skeleton before writing the
    # target JML. Keep those methods available to the design pipeline instead
    # of requiring a pre-existing contract just to discuss one.
    for match in DECLARATION_RE.finditer(_mask_jml_comments(text)):
        signature = re.sub(r"\s+", " ", match.group("signature")).strip()
        key = (match.group("name"), signature)
        if key in seen:
            continue
        result.methods.append(MethodSpec(
            interface=result.name,
            name=match.group("name"),
            signature=signature,
            jml="",
            markers=re.findall(r"\b(pure|safe)\b", match.group("markers")),
        ))
        seen.add(key)
    return result


def find_interface_dir(source_root: Path, profile: dict | None = None) -> Path:
    profile = profile or load_course_profile()
    expected = source_root / Path(profile["interface_relative_dir"])
    if expected.is_dir():
        return expected
    candidates = list(source_root.rglob("NetworkInterface.java"))
    if len(candidates) == 1:
        return candidates[0].parent
    raise FileNotFoundError(f"Cannot uniquely locate official interfaces under {source_root}")


def load_hw9_catalog(source_root: str | Path, profile_path: str | Path | None = None) -> list[InterfaceSpec]:
    profile = load_course_profile(profile_path)
    directory = find_interface_dir(Path(source_root), profile)
    names = profile["interface_files"]
    return [parse_interface(directory / name) for name in names]
