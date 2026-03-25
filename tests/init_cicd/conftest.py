import os
import shutil
import subprocess
from pathlib import Path

import pytest


TESTS_ROOT = Path(__file__).resolve().parent
FIXTURES_ROOT = TESTS_ROOT / "fixtures"
REPO_ROOT = TESTS_ROOT.parents[1]
KIND_CONFIG_PATH = REPO_ROOT / "infrastructure" / "kubernetes" / "kind" / "cluster-config.yaml"
CLUSTER_NAME = "hape"


@pytest.fixture()
def fixture_project_factory(tmp_path: Path):
    def _factory(fixture_name: str) -> Path:
        source_path = FIXTURES_ROOT / fixture_name
        target_path = tmp_path / fixture_name
        shutil.copytree(source_path, target_path)
        return target_path

    return _factory


def _run(command: list[str]) -> subprocess.CompletedProcess:
    return subprocess.run(command, check=True, text=True, capture_output=True)


def _is_functional_test_enabled() -> bool:
    return os.getenv("HAPE_RUN_KUBE_AGENT_FUNCTIONAL_TESTS", "0") == "1"


@pytest.fixture(scope="session")
def functional_kind_cluster() -> dict[str, str | None]:
    if not _is_functional_test_enabled():
        pytest.skip("Set HAPE_RUN_KUBE_AGENT_FUNCTIONAL_TESTS=1 to run init-cicd functional tests.")
    if not shutil.which("kind"):
        pytest.skip("kind is required for init-cicd functional tests.")
    if not shutil.which("kubectl"):
        pytest.skip("kubectl is required for init-cicd functional tests.")
    list_clusters = _run(["kind", "get", "clusters"])
    cluster_names = [line.strip() for line in list_clusters.stdout.splitlines() if line.strip()]
    cluster_created_in_fixture = False
    if CLUSTER_NAME not in cluster_names:
        _run(["kind", "create", "cluster", "--name", CLUSTER_NAME, "--config", str(KIND_CONFIG_PATH)])
        cluster_created_in_fixture = True
    kube_context = f"kind-{CLUSTER_NAME}"
    kubeconfig_path = os.getenv("KUBECONFIG")
    yield {"kube_context": kube_context, "kubeconfig_path": kubeconfig_path}
    if cluster_created_in_fixture:
        _run(["kind", "delete", "cluster", "--name", CLUSTER_NAME])


if __name__ == "__main__":
    print(FIXTURES_ROOT)
