from __future__ import annotations

import shutil
from dataclasses import dataclass
from pathlib import Path
from typing import Protocol

from .composer import CASE_ASSETS, compose_stage


class TextGenerator(Protocol):
    def generate(self, prompt: str) -> str: ...


STAGES = (
    ("analyzer", "analyzer.yaml"),
    ("planner", "plan.md"),
    ("template", "template_plan.json"),
    ("critic", "review.yaml"),
    ("assessment", "assessment_plan.json"),
)


@dataclass
class PipelineResult:
    output_dir: Path
    artifacts: dict[str, Path]


def run_pipeline(
    client: TextGenerator,
    project_root: Path,
    source_root: str,
    case_dir: Path,
    output_dir: Path,
    method_name: str,
    interface_name: str = "NetworkInterface",
) -> PipelineResult:
    output_dir.mkdir(parents=True, exist_ok=True)
    requirement = case_dir / "requirement.md"
    if not requirement.is_file():
        raise FileNotFoundError(f"Case requirement is missing: {requirement}")
    shutil.copyfile(requirement, output_dir / "requirement.md")
    for asset_name in CASE_ASSETS:
        asset = case_dir / asset_name
        if not asset.is_file():
            raise FileNotFoundError(f"Case teacher design asset is missing: {asset}")
        shutil.copyfile(asset, output_dir / asset_name)

    artifacts: dict[str, Path] = {}
    for index, (stage, artifact_name) in enumerate(STAGES, start=1):
        prompt = compose_stage(
            project_root=project_root,
            source_root=source_root,
            case_dir=output_dir,
            stage=stage,
            method_name=method_name,
            interface_name=interface_name,
        )
        prompt_path = output_dir / f"{index:02d}-{stage}-input.md"
        prompt_path.write_text(prompt, encoding="utf-8")
        response = client.generate(prompt).strip() + "\n"
        artifact_path = output_dir / artifact_name
        artifact_path.write_text(response, encoding="utf-8")
        artifacts[stage] = artifact_path
    return PipelineResult(output_dir=output_dir, artifacts=artifacts)
