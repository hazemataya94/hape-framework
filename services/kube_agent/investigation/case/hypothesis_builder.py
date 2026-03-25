from services.kube_agent.investigation.checks.diagnostic_check_models import CheckResult


class HypothesisBuilder:
    def _build_hypothesis(self, check_result: CheckResult) -> str:
        return f"{check_result.check_name}: {check_result.summary}"

    def build(self, check_results: list[CheckResult]) -> list[str]:
        hypotheses: list[str] = []
        for check_result in check_results:
            if check_result.status not in {"matched", "inconclusive"}:
                continue
            hypotheses.append(self._build_hypothesis(check_result=check_result))
        return hypotheses


if __name__ == "__main__":
    print(HypothesisBuilder())
