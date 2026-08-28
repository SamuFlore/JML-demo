from __future__ import annotations

import re
from pathlib import Path

from .model import InterfaceSpec, MethodSpec


INTERFACE_DIR = Path("面向对象第三单元第一次作业官方包/com/oocourse/spec1/main")
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


def _clean_jml(text: str) -> str:
    text = re.sub(r"^/\*@|@?\*/$", "", text.strip())
    text = re.sub(r"^//\s*@\s?", "", text)
    lines = []
    for line in text.splitlines():
        lines.append(re.sub(r"^\s*@\s?", "", line).rstrip())
    return "\n".join(lines).strip()


def _clauses(jml: str, keyword: str) -> list[str]:
    pattern = re.compile(
        rf"(?:^|\n)\s*{keyword}\s+(.*?);(?=\s*(?:\n|$))", re.DOTALL
    )
    return [re.sub(r"\s+", " ", item).strip() for item in pattern.findall(jml)]


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
    return result


def find_interface_dir(source_root: Path) -> Path:
    expected = source_root / INTERFACE_DIR
    if expected.is_dir():
        return expected
    candidates = list(source_root.rglob("NetworkInterface.java"))
    if len(candidates) == 1:
        return candidates[0].parent
    raise FileNotFoundError(f"Cannot uniquely locate official interfaces under {source_root}")


def load_hw9_catalog(source_root: str | Path) -> list[InterfaceSpec]:
    directory = find_interface_dir(Path(source_root))
    names = ["UserInterface.java", "VideoInterface.java", "NetworkInterface.java"]
    return [parse_interface(directory / name) for name in names]
