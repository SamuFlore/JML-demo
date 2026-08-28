"""Deterministic, unified semantic judge for the ``followUser`` JML demo.

This module deliberately evaluates JML, not Java implementations and not LLM
opinions.  It compares a completed student contract with the staff contract on
a finite, course-defined abstract model.  The finite model is the explicit
scope of this demo's semantic claim.
"""

from __future__ import annotations

import copy
import dataclasses
import re
from enum import Enum
from pathlib import Path
from typing import Any


class SpecError(ValueError):
    """A student contract is structurally or syntactically invalid."""


class SemanticDiagnosticCode(str, Enum):
    """Deterministic semantic-feedback codes exposed to students."""

    NORMAL_CONDITION_MISMATCH = "NORMAL_CONDITION_MISMATCH"
    POSTCONDITION_MISMATCH = "POSTCONDITION_MISMATCH"
    EXCEPTION_PARTITION_MISMATCH = "EXCEPTION_PARTITION_MISMATCH"
    LOCKED_CLAUSE_CHANGED = "LOCKED_CLAUSE_CHANGED"
    JML_FORMAT_OR_SYMBOL = "JML_FORMAT_OR_SYMBOL"


@dataclasses.dataclass(frozen=True)
class Token:
    kind: str
    text: str
    offset: int


TOKEN_RE = re.compile(
    r"\s*(?:(?P<JML>\\old)|(?P<OP>&&|\|\||==|!=|<=|>=)|"
    r"(?P<PUNC>[().,;!<>])|(?P<INT>\d+)|"
    r"(?P<IDENT>[A-Za-z_][A-Za-z0-9_]*)|(?P<BAD>.))"
)


def tokenize(source: str) -> list[Token]:
    result: list[Token] = []
    position = 0
    while position < len(source):
        match = TOKEN_RE.match(source, position)
        if match is None:  # Defensive; TOKEN_RE consumes one character.
            raise SpecError(f"无法识别的位置：{position}")
        position = match.end()
        kind = match.lastgroup
        assert kind is not None
        text = match.group(kind)
        if kind == "BAD":
            raise SpecError(f"不支持的字符 {text!r}（位置 {match.start(kind)}）")
        result.append(Token(kind if kind not in {"OP", "PUNC", "JML"} else text, text, match.start(kind)))
    result.append(Token("EOF", "", len(source)))
    return result


class Expr:
    pass


@dataclasses.dataclass(frozen=True)
class Literal(Expr):
    value: Any


@dataclasses.dataclass(frozen=True)
class Variable(Expr):
    name: str


@dataclasses.dataclass(frozen=True)
class Call(Expr):
    name: str
    args: tuple[Expr, ...]


@dataclasses.dataclass(frozen=True)
class Unary(Expr):
    operator: str
    operand: Expr


@dataclasses.dataclass(frozen=True)
class Binary(Expr):
    operator: str
    left: Expr
    right: Expr


@dataclasses.dataclass(frozen=True)
class Old(Expr):
    expression: Expr


class ExpressionParser:
    """Parser for the demo's object-oriented Level-0 JML expression subset."""

    def __init__(self, source: str):
        self.tokens = tokenize(source)
        self.index = 0

    def current(self) -> Token:
        return self.tokens[self.index]

    def accept(self, *kinds: str) -> Token | None:
        if self.current().kind in kinds:
            token = self.current()
            self.index += 1
            return token
        return None

    def expect(self, *kinds: str) -> Token:
        token = self.accept(*kinds)
        if token is None:
            wanted = " 或 ".join(kinds)
            current = self.current()
            raise SpecError(f"期望 {wanted}，但在位置 {current.offset} 得到 {current.text!r}")
        return token

    def parse(self) -> Expr:
        expression = self.parse_or()
        self.expect("EOF")
        return expression

    def parse_or(self) -> Expr:
        expression = self.parse_and()
        while self.accept("||"):
            expression = Binary("||", expression, self.parse_and())
        return expression

    def parse_and(self) -> Expr:
        expression = self.parse_equality()
        while self.accept("&&"):
            expression = Binary("&&", expression, self.parse_equality())
        return expression

    def parse_equality(self) -> Expr:
        expression = self.parse_relational()
        while self.current().kind in {"==", "!="}:
            operator = self.current().kind
            self.index += 1
            expression = Binary(operator, expression, self.parse_relational())
        return expression

    def parse_relational(self) -> Expr:
        expression = self.parse_unary()
        while self.current().kind in {"<", "<=", ">", ">="}:
            operator = self.current().kind
            self.index += 1
            expression = Binary(operator, expression, self.parse_unary())
        return expression

    def parse_unary(self) -> Expr:
        if self.accept("!"):
            return Unary("!", self.parse_unary())
        if self.accept("\\old"):
            self.expect("(")
            expression = self.parse_or()
            self.expect(")")
            return Old(expression)
        return self.parse_primary()

    def parse_primary(self) -> Expr:
        if self.accept("INT"):
            return Literal(int(self.tokens[self.index - 1].text))
        if self.accept("("):
            expression = self.parse_or()
            self.expect(")")
            return expression
        identifier = self.accept("IDENT")
        if identifier is None:
            token = self.current()
            raise SpecError(f"无法在位置 {token.offset} 解析 {token.text!r}")
        if identifier.text == "true":
            expression: Expr = Literal(True)
        elif identifier.text == "false":
            expression = Literal(False)
        elif self.accept("("):
            expression = Call(identifier.text, self.parse_arguments())
        else:
            expression = Variable(identifier.text)
        while self.accept("."):
            member = self.expect("IDENT")
            self.expect("(")
            expression = Call(member.text, (expression, *self.parse_arguments()))
        return expression

    def parse_arguments(self) -> tuple[Expr, ...]:
        arguments: list[Expr] = []
        if self.accept(")"):
            return tuple(arguments)
        while True:
            arguments.append(self.parse_or())
            if self.accept(")"):
                return tuple(arguments)
            self.expect(",")


@dataclasses.dataclass
class State:
    users: set[int]
    following: dict[int, set[int]]
    followers: dict[int, set[int]]

    def copy(self) -> "State":
        return copy.deepcopy(self)

    def follows(self, first: int, second: int) -> bool:
        return second in self.following.get(first, set())

    def is_follower(self, user: int, follower: int) -> bool:
        return follower in self.followers.get(user, set())


@dataclasses.dataclass(frozen=True)
class UserRef:
    user_id: int


@dataclasses.dataclass(frozen=True)
class EvalContext:
    pre: State
    post: State
    arguments: dict[str, int]
    current: State

    def pre_state(self) -> "EvalContext":
        return dataclasses.replace(self, current=self.pre)


ALLOWED_CALLS = {"containsUser", "getUser", "isFollowing", "containsFollower"}


def validate_calls(expression: Expr) -> None:
    if isinstance(expression, Call):
        if expression.name not in ALLOWED_CALLS:
            raise SpecError(f"不允许调用接口外函数：{expression.name}")
        for argument in expression.args:
            validate_calls(argument)
    elif isinstance(expression, (Unary, Old)):
        validate_calls(expression.operand if isinstance(expression, Unary) else expression.expression)
    elif isinstance(expression, Binary):
        validate_calls(expression.left)
        validate_calls(expression.right)


def evaluate(expression: Expr, context: EvalContext) -> Any:
    if isinstance(expression, Literal):
        return expression.value
    if isinstance(expression, Variable):
        if expression.name in context.arguments:
            return context.arguments[expression.name]
        raise SpecError(f"未定义的变量：{expression.name}")
    if isinstance(expression, Old):
        return evaluate(expression.expression, context.pre_state())
    if isinstance(expression, Unary):
        return not bool(evaluate(expression.operand, context))
    if isinstance(expression, Binary):
        if expression.operator == "&&":
            return bool(evaluate(expression.left, context)) and bool(evaluate(expression.right, context))
        if expression.operator == "||":
            return bool(evaluate(expression.left, context)) or bool(evaluate(expression.right, context))
        left = evaluate(expression.left, context)
        right = evaluate(expression.right, context)
        return {
            "==": lambda: left == right,
            "!=": lambda: left != right,
            "<": lambda: left < right,
            "<=": lambda: left <= right,
            ">": lambda: left > right,
            ">=": lambda: left >= right,
        }[expression.operator]()
    if isinstance(expression, Call):
        values = [evaluate(argument, context) for argument in expression.args]
        if expression.name == "containsUser" and len(values) == 1:
            return int(values[0]) in context.current.users
        if expression.name == "getUser" and len(values) == 1:
            return UserRef(int(values[0]))
        if expression.name == "isFollowing" and len(values) == 2 and all(isinstance(v, UserRef) for v in values):
            return context.current.follows(values[0].user_id, values[1].user_id)
        if expression.name == "containsFollower" and len(values) == 2 and all(isinstance(v, UserRef) for v in values):
            return context.current.is_follower(values[0].user_id, values[1].user_id)
        raise SpecError(f"函数 {expression.name} 的参数不符合 followUser 受限语法")
    raise SpecError(f"未知表达式节点：{type(expression).__name__}")


@dataclasses.dataclass(frozen=True)
class Clause:
    kind: str
    body: str
    line: int


def extract_jml_block(java_source: str, method_name: str) -> str:
    blocks = list(re.finditer(r"/\*@(?P<body>.*?)@\*/", java_source, re.DOTALL))
    method_pattern = re.compile(r"\b" + re.escape(method_name) + r"\s*\(")
    declaration = method_pattern.search(java_source)
    if declaration is None:
        raise SpecError(f"未找到方法 {method_name} 的 Java 声明")
    # ``public /*@ safe @*/ void method`` places a marker block between the
    # method specification and the Java declaration.  Choose the nearest
    # preceding *behavioural* JML block, not that marker.
    for block in reversed(blocks):
        if block.end() > declaration.start():
            continue
        body = block.group("body")
        if re.search(r"\b(?:requires|ensures|signals|assignable)\b", body):
            return body
    raise SpecError(f"未找到紧邻方法 {method_name} 的 JML 注释块")


def extract_clauses(block: str) -> list[Clause]:
    """Extract multiline method clauses, preserving the condition body."""
    cleaned_lines = [re.sub(r"^\s*@\s?", "", line).rstrip() for line in block.splitlines()]
    cleaned = "\n".join(cleaned_lines)
    starts = list(re.finditer(r"(?m)^\s*(requires|ensures|signals|assignable)\b\s*", cleaned))
    clauses: list[Clause] = []
    for start in starts:
        depth = 0
        index = start.end()
        while index < len(cleaned):
            char = cleaned[index]
            if char in "(":
                depth += 1
            elif char in ")":
                depth = max(0, depth - 1)
            elif char == ";" and depth == 0:
                body = re.sub(r"\s+", " ", cleaned[start.end():index]).strip()
                line = cleaned.count("\n", 0, start.start()) + 1
                clauses.append(Clause(start.group(1), body, line))
                break
            index += 1
        else:
            raise SpecError(f"第 {cleaned.count(chr(10), 0, start.start()) + 1} 行的 {start.group(1)} 子句缺少分号")
    return clauses


@dataclasses.dataclass(frozen=True)
class MethodContract:
    requires: Expr
    ensures: tuple[Expr, ...]
    signals: tuple[tuple[str, Expr], ...]
    assignables: tuple[str, ...]
    output_ensures: tuple[str, ...]


def parse_contract(java_source: str, method_name: str = "followUser") -> MethodContract:
    if "{{" in java_source:
        raise SpecError("仍有未填写的空位")
    clauses = extract_clauses(extract_jml_block(java_source, method_name))
    requires = [clause for clause in clauses if clause.kind == "requires"]
    if len(requires) != 1:
        raise SpecError("followUser 模板必须恰有一个 normal_behavior 的 requires 子句")
    try:
        requires_expr = ExpressionParser(requires[0].body).parse()
        validate_calls(requires_expr)
    except SpecError as error:
        raise SpecError(f"第 {requires[0].line} 行 requires：{error}") from error

    ensures: list[Expr] = []
    outputs: list[str] = []
    for clause in (item for item in clauses if item.kind == "ensures"):
        if clause.body.startswith("(* output->"):
            outputs.append(clause.body)
            continue
        try:
            expression = ExpressionParser(clause.body).parse()
            validate_calls(expression)
            ensures.append(expression)
        except SpecError as error:
            raise SpecError(f"第 {clause.line} 行 ensures：{error}") from error
    if len(ensures) != 2:
        raise SpecError("followUser 模板必须恰有两个可评测的 ensures 子句")

    signals: list[tuple[str, Expr]] = []
    for clause in (item for item in clauses if item.kind == "signals"):
        match = re.match(r"^\((?P<exception>[A-Za-z_]\w*)\s+[A-Za-z_]\w*\)\s*(?P<condition>.+)$", clause.body)
        if match is None:
            raise SpecError(f"第 {clause.line} 行 signals：异常声明格式错误")
        try:
            expression = ExpressionParser(match.group("condition")).parse()
            validate_calls(expression)
            signals.append((match.group("exception"), expression))
        except SpecError as error:
            raise SpecError(f"第 {clause.line} 行 signals：{error}") from error
    if len(signals) != 4:
        raise SpecError("followUser 模板必须恰有四个 signals 子句")
    return MethodContract(
        requires=requires_expr,
        ensures=tuple(ensures),
        signals=tuple(signals),
        assignables=tuple(item.body for item in clauses if item.kind == "assignable"),
        output_ensures=tuple(outputs),
    )


@dataclasses.dataclass(frozen=True)
class Scenario:
    pre: State
    post: State
    arguments: dict[str, int]

    def context(self) -> EvalContext:
        return EvalContext(self.pre, self.post, self.arguments, self.post)


def _state(users: set[int], edges: set[tuple[int, int]] = set()) -> State:
    following = {user: set() for user in users}
    followers = {user: set() for user in users}
    for first, second in edges:
        following.setdefault(first, set()).add(second)
        followers.setdefault(second, set()).add(first)
    return State(set(users), following, followers)


def pre_state_scenarios() -> list[Scenario]:
    """All category-distinguishing pre-states for the followUser demo."""
    steady = _state({1, 2, 3}, {(3, 1)})
    return [
        Scenario(steady, steady.copy(), {"id1": 1, "id2": 2}),
        Scenario(_state(set()), _state(set()), {"id1": 1, "id2": 2}),
        Scenario(_state({2}), _state({2}), {"id1": 1, "id2": 2}),
        Scenario(_state({1}), _state({1}), {"id1": 1, "id2": 2}),
        Scenario(_state(set()), _state(set()), {"id1": 1, "id2": 1}),
        Scenario(_state({1}), _state({1}), {"id1": 1, "id2": 1}),
        Scenario(_state({1}, {(1, 1)}), _state({1}, {(1, 1)}), {"id1": 1, "id2": 1}),
        Scenario(_state({1, 2}), _state({1, 2}, {(1, 2)}), {"id1": 1, "id2": 2}),
        Scenario(_state({1, 2}), _state({1, 2}), {"id1": 1, "id2": 2}),
    ]


def post_state_scenarios() -> list[Scenario]:
    pre = _state({1, 2, 3}, {(3, 1)})
    correct = _state({1, 2, 3}, {(3, 1), (1, 2)})
    only_following = _state({1, 2, 3}, {(3, 1), (1, 2)})
    only_following.followers[2].remove(1)
    only_followers = _state({1, 2, 3}, {(3, 1)})
    only_followers.followers[2].add(1)
    reversed_relation = _state({1, 2, 3}, {(3, 1), (2, 1)})
    return [
        Scenario(pre, correct, {"id1": 1, "id2": 2}),
        Scenario(pre, only_following, {"id1": 1, "id2": 2}),
        Scenario(pre, only_followers, {"id1": 1, "id2": 2}),
        Scenario(pre, reversed_relation, {"id1": 1, "id2": 2}),
    ]


@dataclasses.dataclass(frozen=True)
class Diagnostic:
    code: str
    location: str
    category: str
    observation: str
    guidance: str

    def to_dict(self) -> dict[str, str]:
        return dataclasses.asdict(self)


@dataclasses.dataclass(frozen=True)
class SemanticResult:
    score: int
    passed: bool
    diagnostics: tuple[Diagnostic, ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "score": self.score,
            "passed": self.passed,
            "diagnostics": [item.to_dict() for item in self.diagnostics],
        }


def _mismatch(reference: Expr, candidate: Expr, scenarios: list[Scenario]) -> bool:
    return any(bool(evaluate(reference, scenario.context())) != bool(evaluate(candidate, scenario.context())) for scenario in scenarios)


def evaluate_contracts(reference: MethodContract, candidate: MethodContract) -> SemanticResult:
    diagnostics: list[Diagnostic] = []
    obligations = 7  # One requires, two ensures, and four signals conditions.
    passed_obligations = 0
    if _mismatch(reference.requires, candidate.requires, pre_state_scenarios()):
        diagnostics.append(Diagnostic(
            SemanticDiagnosticCode.NORMAL_CONDITION_MISMATCH.value, "NORMAL_CONDITION", "正常行为条件",
            "存在前态使你的正常行为条件与标准合同的行为分类不一致。",
            "检查正常执行是否同时排除了缺失用户、自关注和重复关注。",
        ))
    else:
        passed_obligations += 1

    labels = ("FORWARD_POSTCONDITION", "INVERSE_POSTCONDITION")
    for index, label in enumerate(labels):
        if _mismatch(reference.ensures[index], candidate.ensures[index], post_state_scenarios()):
            diagnostics.append(Diagnostic(
                SemanticDiagnosticCode.POSTCONDITION_MISMATCH.value, label, "后置状态关系",
                "某个成功后的抽象状态被你的后置条件错误接受或拒绝。",
                "核对关注关系的方向，以及该空应描述的是关注还是粉丝关系。",
            ))
        else:
            passed_obligations += 1

    signal_labels = ("FIRST_USER_MISSING", "SECOND_USER_MISSING", "SELF_FOLLOW", "DUPLICATE_FOLLOW")
    for index, label in enumerate(signal_labels):
        reference_exception, reference_expression = reference.signals[index]
        candidate_exception, candidate_expression = candidate.signals[index]
        if candidate_exception != reference_exception or _mismatch(reference_expression, candidate_expression, pre_state_scenarios()):
            diagnostics.append(Diagnostic(
                SemanticDiagnosticCode.EXCEPTION_PARTITION_MISMATCH.value, label, "异常分支与优先级",
                "该异常分支在某些前态下的匹配结果或异常类型与标准合同不一致。",
                "检查该分支是否覆盖了自己的情形，并正确排除了更早的异常情形。",
            ))
        else:
            passed_obligations += 1

    if reference.assignables != candidate.assignables or reference.output_ensures != candidate.output_ensures:
        diagnostics.append(Diagnostic(
            SemanticDiagnosticCode.LOCKED_CLAUSE_CHANGED.value, "LOCKED_FRAME_OR_OUTPUT", "锁定规格被修改",
            "assignable 或成功输出规格与模板中的锁定内容不一致。",
            "仅填写分配给学生的空位，不要修改锁定子句。",
        ))
        obligations += 1
    else:
        obligations += 1
        passed_obligations += 1
    score = round(100 * passed_obligations / obligations)
    return SemanticResult(score, not diagnostics, tuple(diagnostics))


def evaluate_sources(reference_source: str, student_source: str, method_name: str = "followUser") -> SemanticResult:
    try:
        reference = parse_contract(reference_source, method_name)
        candidate = parse_contract(student_source, method_name)
    except SpecError as error:
        return SemanticResult(0, False, (Diagnostic(
            SemanticDiagnosticCode.JML_FORMAT_OR_SYMBOL.value, "SUBMISSION", "JML 格式或接口符号",
            str(error), "检查空位是否填完、JML 语法是否完整，以及是否只使用模板允许的接口符号。",
        ),))
    return evaluate_contracts(reference, candidate)


def evaluate_files(reference: Path, student: Path, method_name: str = "followUser") -> SemanticResult:
    return evaluate_sources(reference.read_text(encoding="utf-8"), student.read_text(encoding="utf-8"), method_name)
