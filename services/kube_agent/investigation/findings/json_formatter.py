import json

from services.kube_agent.investigation.findings.findings_models import Findings


class JsonFormatter:
    @staticmethod
    def format(findings: Findings) -> str:
        return json.dumps(findings.__dict__, indent=2, sort_keys=True, default=str)


if __name__ == "__main__":
    print(JsonFormatter())
