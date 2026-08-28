from __future__ import annotations

import json
from pathlib import Path

from .parser import load_hw9_catalog


STAGE_CONFIG = {
    "analyzer": {
        "prompt": "analyzer.md",
        "skills": ["hw9_domain.md"],
        "artifacts": [],
    },
    "planner": {
        "prompt": "planner.md",
        "skills": ["jml_level0.md", "spec_patterns.md"],
        "artifacts": ["analyzer.yaml"],
    },
    "generator": {
        "prompt": "generator.md",
        "skills": ["jml_level0.md"],
        "artifacts": ["analyzer.yaml", "plan.md"],
    },
    "critic": {
        "prompt": "critic.md",
        "skills": ["critic_checklist.md"],
        "artifacts": ["analyzer.yaml", "plan.md", "spec.jml"],
    },
}


def _find_method(source_root: str, method_name: str, interface_name: str):
    matches = [
        method
        for interface in load_hw9_catalog(source_root)
        for method in interface.methods
        if method.name == method_name and method.interface == interface_name
    ]
    if len(matches) != 1:
        raise ValueError(
            f"Expected one {interface_name}.{method_name}, found {len(matches)}"
        )
    return matches[0]


def compose_stage(
    project_root: Path,
    source_root: str,
    case_dir: Path,
    stage: str,
    method_name: str,
    interface_name: str = "NetworkInterface",
) -> str:
    config = STAGE_CONFIG[stage]
    method = _find_method(source_root, method_name, interface_name)
    sections = [
        f"# HW9 Specification Agent — {stage.title()} Stage",
        "## Stage instructions\n\n" + (project_root / "prompts" / config["prompt"]).read_text(encoding="utf-8"),
    ]
    for skill_name in config["skills"]:
        skill = (project_root / "skills" / skill_name).read_text(encoding="utf-8")
        sections.append(f"## Skill: {skill_name}\n\n{skill}")
    requirement = (case_dir / "requirement.md").read_text(encoding="utf-8")
    sections.append("## Original requirement\n\n" + requirement)
    sections.append(
        "## Official interface grounding\n\n```json\n"
        + json.dumps(method.to_dict(), ensure_ascii=False, indent=2)
        + "\n```"
    )
    for artifact_name in config["artifacts"]:
        path = case_dir / artifact_name
        if not path.is_file():
            raise FileNotFoundError(f"Required prior-stage artifact is missing: {path}")
        sections.append(f"## Prior artifact: {artifact_name}\n\n{path.read_text(encoding='utf-8')}")
    sections.append("## Your response\n\nReturn only the output required by the stage instructions.")
    return "\n\n---\n\n".join(sections) + "\n"

