from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class CheckResult:
    check_name: str
    status: str
    confidence: str
    summary: str
    evidence_keys: list[str] = field(default_factory=list)
    details: dict[str, Any] = field(default_factory=dict)


if __name__ == "__main__":
    print(CheckResult(check_name="oom-kill-check", status="matched", confidence="high", summary="Container terminated with OOMKilled."))
