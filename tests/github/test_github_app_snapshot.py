from __future__ import annotations

import json
from pathlib import Path

import pytest

from services.github_app_service import GitHubAppError, GitHubAppService

FIXTURES_PATH = Path(__file__).resolve().parents[4] / "platform/agent/hape-platform-agent-planning/contracts/github-authority/v1.20.0/fixtures.json"


def _fixtures() -> dict[str, object]:
    return json.loads(FIXTURES_PATH.read_text(encoding="utf-8"))


def _file_bytes(item: dict[str, object]) -> bytes:
    if "hexBytes" in item:
        return bytes.fromhex(str(item["hexBytes"]))
    return str(item.get("bytes", "")).encode("utf-8")


def test_admitted_snapshot_digests_match_frozen_fixtures() -> None:
    fixtures = _fixtures()
    snapshots = fixtures["snapshots"]
    service = GitHubAppService()
    for name in ("readmeOnly", "helloAndReadme", "emptyFile", "executable", "binaryPng", "unicodeNfc"):
        snapshot = snapshots[name]
        files = [{"path": item["path"], "mode": item["mode"], "bytes": _file_bytes(item)} for item in snapshot["files"]]
        _, digest = service.admit_local_files(files)
        assert digest == snapshot["aggregateDigest"]


def test_snapshot_rejections_match_frozen_reasons() -> None:
    service = GitHubAppService()
    cases = [
        ([{"path": "link", "mode": "120000", "bytes": b"target"}], "symlink"),
        ([{"path": "vendor", "mode": "160000", "bytes": b""}], "submodule"),
        ([{"path": "big.bin", "mode": "100644", "bytes": b"version https://git-lfs.github.com/spec/v1\n"}], "lfs_pointer"),
        ([{"path": ".git/config", "mode": "100644", "bytes": b"x"}], "dot_git_segment"),
        ([{"path": "../secret", "mode": "100644", "bytes": b"x"}], "path_traversal"),
        ([{"path": "README.md", "mode": "100644", "bytes": b"a"}, {"path": "readme.md", "mode": "100644", "bytes": b"b"}], "case_collision"),
        ([{"path": "cafe\u0301.txt", "mode": "100644", "bytes": b"ok\n"}], "unicode_nfc_mismatch"),
        ([{"path": "secret.txt", "mode": "100644", "bytes": b"ghp_exampleHighConfidenceSecretValue"}], "high_confidence_secret"),
        ([{"path": "huge.bin", "mode": "100644", "bytes": b"x" * 1048577}], "oversized_file"),
    ]
    for files, _reason in cases:
        with pytest.raises(GitHubAppError) as exc:
            service.admit_local_files(files)
        assert exc.value.code == "snapshot_rejected"


def test_too_many_files_is_rejected() -> None:
    service = GitHubAppService()
    files = [{"path": f"f{index}.txt", "mode": "100644", "bytes": b"x"} for index in range(2001)]
    with pytest.raises(GitHubAppError) as exc:
        service.admit_local_files(files)
    assert exc.value.code == "snapshot_rejected"


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__]))
