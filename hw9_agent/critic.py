from __future__ import annotations

from .model import Analysis, Finding, MethodSpec


def review(method: MethodSpec) -> list[Finding]:
    findings: list[Finding] = []
    is_pure = "pure" in method.markers

    if is_pure and method.assignable and any(x != r"\nothing" for x in method.assignable):
        findings.append(Finding(
            "error", "PURE_FRAME_CONFLICT",
            "方法标记为 pure，但 assignable 允许修改状态。",
        ))
    if is_pure and not method.assignable:
        findings.append(Finding(
            "info", "PURE_IMPLICIT_FRAME",
            "pure 方法未显式写 assignable \\nothing；测试仍应验证调用前后状态一致。",
        ))
    if "safe" in method.markers and not method.assignable:
        findings.append(Finding(
            "warning", "SAFE_WITHOUT_FRAME",
            "safe 方法没有显式 assignable，需结合课程对 safe 的扩展语义检查副作用边界。",
        ))
    if "exceptional_behavior" in method.behavior_kinds and not method.signals:
        findings.append(Finding(
            "error", "EXCEPTION_WITHOUT_SIGNALS",
            "声明了 exceptional_behavior，但没有解析到 signals 子句。",
        ))
    if "normal_behavior" in method.behavior_kinds and not method.ensures:
        findings.append(Finding(
            "warning", "NORMAL_WITHOUT_ENSURES",
            "声明了 normal_behavior，但没有解析到 ensures 子句。",
        ))
    if len(method.signals) > 1:
        findings.append(Finding(
            "info", "EXCEPTION_PRIORITY",
            "存在多个异常分支，应按 signals 条件的排他化顺序测试异常优先级。",
        ))
    if not findings:
        findings.append(Finding("info", "NO_STATIC_CONFLICT", "未发现基础结构冲突。"))
    return findings


def test_obligations(method: MethodSpec) -> list[str]:
    obligations: list[str] = []
    for index, condition in enumerate(method.requires, start=1):
        obligations.append(f"正常分支 {index}：构造满足 `{condition}` 的状态并验证所有 ensures。")
    if method.ensures and not method.requires:
        obligations.append("无前置条件正常分支：覆盖空状态、最小状态和非平凡状态。")
    for signal in method.signals:
        obligations.append(f"异常分支：触发 `{signal}`，验证异常类型及调用前后状态原子性。")
    if "pure" in method.markers or r"\nothing" in method.assignable:
        obligations.append("副作用：深度快照 Network 及内部对象，重复调用后状态必须完全一致。")
    if "\\sum" in method.jml or "\\num_of" in method.jml:
        obligations.append("聚合边界：覆盖空集合、单元素、全命中、零命中与混合命中。")
    if "\\exists" in method.jml or "\\forall" in method.jml:
        obligations.append("量词边界：覆盖空容器，并构造仅首项、仅末项满足条件的样例。")
    if "path" in method.jml.lower():
        obligations.append("图结构：覆盖自身、直达、多跳、环、不可达以及多条不同长度路径。")
    return obligations


def analyze(method: MethodSpec) -> Analysis:
    return Analysis(method=method, findings=review(method), test_obligations=test_obligations(method))

