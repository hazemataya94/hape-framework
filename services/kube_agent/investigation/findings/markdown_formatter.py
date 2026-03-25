from services.kube_agent.investigation.findings.findings_models import Findings


class MarkdownFormatter:
    @staticmethod
    def _format_links(findings: Findings) -> str:
        if not findings.dashboard_links:
            return "- none"
        return "\n".join([f"- [{name}]({url})" for name, url in findings.dashboard_links.items()])

    @staticmethod
    def _format_list(items: list[str]) -> str:
        if not items:
            return "- none"
        return "\n".join([f"- {item}" for item in items])

    def format(self, findings: Findings) -> str:
        root_cause = findings.likely_root_cause or "unknown"
        return (
            f"# {findings.title}\n\n"
            f"## Summary\n{findings.summary}\n\n"
            f"## Likely Root Cause\n{root_cause}\n\n"
            f"## Evidence Summary\n{self._format_list(findings.evidence_summary)}\n\n"
            f"## Debugging Steps\n{self._format_list(findings.debugging_steps)}\n\n"
            f"## Suggested Fixes\n{self._format_list(findings.suggested_fixes)}\n\n"
            f"## Dashboard Links\n{self._format_links(findings)}\n\n"
            f"## AI Used\n{findings.ai_used}\n"
        )


if __name__ == "__main__":
    print(MarkdownFormatter())
