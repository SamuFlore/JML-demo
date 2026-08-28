"""Command-line entrypoint for the unified followUser semantic evaluation."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from semantic_judge import SpecError, evaluate_files


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser(description="Unit 3 followUser 统一 JML 语义评测")
    parser.add_argument("java_source", type=Path, help="学生填写后的 Java 接口文件")
    parser.add_argument("--reference", type=Path, required=True, help="服务器端完整参考 JML 接口")
    parser.add_argument("--method", default="followUser", help="要评测的方法")
    parser.add_argument("--json", action="store_true", help="输出结构化诊断 JSON")
    args = parser.parse_args()
    try:
        result = evaluate_files(args.reference, args.java_source, args.method)
    except (OSError, SpecError) as error:
        print(f"规格评测配置错误：{error}", file=sys.stderr)
        return 2
    if args.json:
        print(json.dumps(result.to_dict(), ensure_ascii=False))
    elif result.passed:
        print("规格评测通过：全部语义义务均满足。")
    else:
        print(f"规格评测未通过：得分 {result.score}")
        for item in result.diagnostics:
            print(f"- [{item.location}] {item.category}：{item.observation}")
            print(f"  建议：{item.guidance}")
    return 0 if result.passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
