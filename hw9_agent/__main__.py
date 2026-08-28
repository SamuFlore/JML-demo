from __future__ import annotations

import argparse
import json
import os
from pathlib import Path

from .client import DeepSeekChatClient, ModelClientError
from .critic import analyze
from .composer import STAGE_CONFIG, compose_stage
from .exercise import ExerciseBundle, build_review_prompt, deterministic_check, interactive_session
from .parser import load_hw9_catalog
from .pipeline import run_pipeline
from .webapp import ExerciseWebApp, serve


def _all_methods(catalog):
    for interface in catalog:
        yield from interface.methods


def main() -> None:
    parser = argparse.ArgumentParser(description="OO U3 HW9 JML specification agent")
    sub = parser.add_subparsers(dest="command", required=True)
    list_parser = sub.add_parser("list", help="list parsed interface methods")
    list_parser.add_argument("--source-root", required=True)
    inspect_parser = sub.add_parser("inspect", help="analyze one method specification")
    inspect_parser.add_argument("--source-root", required=True)
    inspect_parser.add_argument("--method", required=True)
    inspect_parser.add_argument("--interface", help="optional interface name for ambiguous methods")
    inspect_parser.add_argument("--json", action="store_true")
    prepare_parser = sub.add_parser("prepare", help="compose a model-ready stage prompt")
    prepare_parser.add_argument("--source-root", required=True)
    prepare_parser.add_argument("--case-dir", required=True)
    prepare_parser.add_argument("--stage", choices=STAGE_CONFIG, required=True)
    prepare_parser.add_argument("--method", required=True)
    prepare_parser.add_argument("--interface", default="NetworkInterface")
    prepare_parser.add_argument("--output", help="optional output Markdown path")
    run_parser = sub.add_parser("run", help="run all four stages with the DeepSeek API")
    run_parser.add_argument("--source-root", required=True)
    run_parser.add_argument("--case-dir", required=True)
    run_parser.add_argument("--method", required=True)
    run_parser.add_argument("--interface", default="NetworkInterface")
    run_parser.add_argument("--output-dir", required=True)
    run_parser.add_argument("--model", default=os.environ.get("DEEPSEEK_MODEL", "deepseek-chat"))
    run_parser.add_argument("--base-url", default=os.environ.get("DEEPSEEK_BASE_URL", "https://api.deepseek.com"))
    exercise_parser = sub.add_parser("exercise", help="review a student's JML fill-in submission")
    exercise_parser.add_argument("--source-root", required=True)
    exercise_parser.add_argument("--exercise-dir", required=True)
    exercise_parser.add_argument("--mode", choices=("hint", "review", "solution"), default="hint")
    exercise_parser.add_argument("--submission", help="one-shot submission file; omit for interactive mode")
    exercise_parser.add_argument("--offline", action="store_true", help="run deterministic checks only")
    exercise_parser.add_argument("--model", default=os.environ.get("DEEPSEEK_MODEL", "deepseek-chat"))
    exercise_parser.add_argument("--base-url", default=os.environ.get("DEEPSEEK_BASE_URL", "https://api.deepseek.com"))
    web_parser = sub.add_parser("web", help="start the local JML learning web interface")
    web_parser.add_argument("--source-root", required=True)
    web_parser.add_argument("--exercise-dir", required=True)
    web_parser.add_argument("--host", default="127.0.0.1")
    web_parser.add_argument("--port", type=int, default=8000)
    web_parser.add_argument("--model", default=os.environ.get("DEEPSEEK_MODEL", "deepseek-chat"))
    web_parser.add_argument("--base-url", default=os.environ.get("DEEPSEEK_BASE_URL", "https://api.deepseek.com"))
    args = parser.parse_args()

    catalog = load_hw9_catalog(args.source_root)
    methods = list(_all_methods(catalog))
    if args.command == "prepare":
        project_root = Path(__file__).resolve().parent.parent
        content = compose_stage(
            project_root=project_root,
            source_root=args.source_root,
            case_dir=Path(args.case_dir),
            stage=args.stage,
            method_name=args.method,
            interface_name=args.interface,
        )
        if args.output:
            output = Path(args.output)
            output.parent.mkdir(parents=True, exist_ok=True)
            output.write_text(content, encoding="utf-8")
            print(output.resolve())
        else:
            print(content, end="")
        return
    if args.command == "run":
        try:
            client = DeepSeekChatClient(model=args.model, base_url=args.base_url)
            result = run_pipeline(
                client=client,
                project_root=Path(__file__).resolve().parent.parent,
                source_root=args.source_root,
                case_dir=Path(args.case_dir),
                output_dir=Path(args.output_dir),
                method_name=args.method,
                interface_name=args.interface,
            )
        except ModelClientError as exc:
            raise SystemExit(str(exc)) from exc
        print(result.output_dir.resolve())
        for stage, path in result.artifacts.items():
            print(f"{stage}: {path.resolve()}")
        return
    if args.command == "exercise":
        project_root = Path(__file__).resolve().parent.parent
        bundle = ExerciseBundle.load(Path(args.exercise_dir))
        if args.submission:
            submission = Path(args.submission).read_text(encoding="utf-8")
            checks = deterministic_check(bundle, submission)
            if args.offline:
                print(json.dumps(checks, ensure_ascii=False, indent=2))
                return
            try:
                client = DeepSeekChatClient(model=args.model, base_url=args.base_url)
                prompt = build_review_prompt(
                    project_root, args.source_root, bundle, submission, args.mode, []
                )
                print(client.generate(prompt))
            except ModelClientError as exc:
                raise SystemExit(str(exc)) from exc
            return
        if args.offline:
            raise SystemExit("--offline requires --submission")
        try:
            client = DeepSeekChatClient(model=args.model, base_url=args.base_url)
            interactive_session(client, project_root, args.source_root, bundle, args.mode)
        except ModelClientError as exc:
            raise SystemExit(str(exc)) from exc
        return
    if args.command == "web":
        app = ExerciseWebApp(
            project_root=Path(__file__).resolve().parent.parent,
            source_root=args.source_root,
            exercise_dir=Path(args.exercise_dir),
            model=args.model,
            base_url=args.base_url,
        )
        serve(app, args.host, args.port)
        return
    if args.command == "list":
        for method in methods:
            print(f"{method.interface}.{method.name}: {method.signature}")
        return

    matches = [
        method for method in methods
        if method.name == args.method
        and (not args.interface or method.interface == args.interface)
    ]
    if not matches:
        available = ", ".join(sorted({method.name for method in methods}))
        raise SystemExit(f"Unknown method {args.method}. Available: {available}")
    if len(matches) > 1:
        choices = ", ".join(method.interface for method in matches)
        raise SystemExit(
            f"Method name {args.method} is ambiguous ({choices}); pass --interface"
        )
    result = analyze(matches[0])
    if args.json:
        print(json.dumps(result.to_dict(), ensure_ascii=False, indent=2))
        return

    method = result.method
    print(f"# {method.interface}.{method.name}")
    print(f"signature: {method.signature}")
    print(f"markers: {', '.join(method.markers) or 'none'}")
    print(f"requires: {len(method.requires)} | ensures: {len(method.ensures)} | signals: {len(method.signals)}")
    print("\n## Critic")
    for item in result.findings:
        print(f"- [{item.severity}] {item.code}: {item.message}")
    print("\n## Test obligations")
    for item in result.test_obligations:
        print(f"- {item}")


if __name__ == "__main__":
    main()
