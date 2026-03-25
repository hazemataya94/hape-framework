from services.kube_agent.investigation.findings.findings_models import Findings


class SlackFormatter:
    def format(self, findings: Findings) -> str:
        root_cause = findings.likely_root_cause or "unknown"
        first_fix = findings.suggested_fixes[0] if findings.suggested_fixes else "No suggested fix available."
        return (
            f"*{findings.title}*\n"
            f"*Summary:* {findings.summary}\n"
            f"*Likely root cause:* {root_cause}\n"
            f"*Suggested fix:* {first_fix}\n"
            f"*AI used:* {findings.ai_used}"
        )


if __name__ == "__main__":
    print(SlackFormatter())
