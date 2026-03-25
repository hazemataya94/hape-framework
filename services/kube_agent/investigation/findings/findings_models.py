from dataclasses import dataclass, field


@dataclass(frozen=True)
class Findings:
    incident_id: str
    title: str
    summary: str
    likely_root_cause: str | None
    evidence_summary: list[str] = field(default_factory=list)
    debugging_steps: list[str] = field(default_factory=list)
    suggested_fixes: list[str] = field(default_factory=list)
    dashboard_links: dict[str, str] = field(default_factory=dict)
    ai_used: bool = False


if __name__ == "__main__":
    print(Findings(incident_id="example", title="Example incident", summary="Example summary", likely_root_cause=None))
