from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass
class MethodSpec:
    interface: str
    name: str
    signature: str
    jml: str
    markers: list[str] = field(default_factory=list)
    requires: list[str] = field(default_factory=list)
    assignable: list[str] = field(default_factory=list)
    ensures: list[str] = field(default_factory=list)
    signals: list[str] = field(default_factory=list)
    behavior_kinds: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class InterfaceSpec:
    name: str
    source: str
    models: list[str] = field(default_factory=list)
    invariants: list[str] = field(default_factory=list)
    methods: list[MethodSpec] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class Finding:
    severity: str
    code: str
    message: str

    def to_dict(self) -> dict[str, str]:
        return asdict(self)


@dataclass
class Analysis:
    method: MethodSpec
    findings: list[Finding]
    test_obligations: list[str]

    def to_dict(self) -> dict[str, Any]:
        return {
            "method": self.method.to_dict(),
            "findings": [item.to_dict() for item in self.findings],
            "test_obligations": self.test_obligations,
        }

