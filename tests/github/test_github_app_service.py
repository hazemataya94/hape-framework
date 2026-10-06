from __future__ import annotations

from datetime import datetime, timezone
import hashlib
from typing import Any

import pytest

from clients.github_app_client import GitHubAppClientError, GitHubAppRegistration
from services.github_app_service import GitHubAppError, GitHubAppService, VaultAgentMemoryCredentialSink

CLOCK = datetime(2026, 9, 13, 10, 0, tzinfo=timezone.utc)


class FixtureGitHubAppClient:
    def __init__(self) -> None:
        self.request_log: list[dict[str, Any]] = []
        self.permissions = {
            "source-read": {"metadata": "read", "contents": "read"},
            "managed-write": {"contents": "write", "administration": "write"},
        }
        self.installations = {
            101: {"id": 101, "suspended_at": None, "account": {"id": 303, "login": "example-user"}, "target_type": "User"},
        }
        self.repositories = [
            {
                "id": 202,
                "name": "source-repo",
                "private": True,
                "visibility": "private",
                "fork": False,
                "archived": False,
                "disabled": False,
                "size": 12,
                "owner": {"id": 303},
            },
            {"id": 203, "name": "hidden-repo", "hape_class": "hidden", "private": True, "size": 1, "owner": {"id": 303}},
            {"id": 204, "name": "archived-repo", "archived": True, "private": True, "size": 1, "owner": {"id": 303}},
        ]
        self.commits = {
            "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa": {
                "sha": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
                "commit": {"tree": {"sha": "tree-readme"}},
            }
        }
        self.trees = {
            "tree-readme": {
                "truncated": False,
                "tree": [{"path": "README.md", "mode": "100644", "type": "blob", "sha": "blob-readme"}],
            }
        }
        self.blobs = {"blob-readme": {"encoding": "utf-8", "content": "# Example\n"}}
        self.created_repos: list[dict[str, Any]] = []
        self.added_collaborators: list[dict[str, Any]] = []
        self.resolved_logins = {"operator@example.com": "octocat"}
        self.refs: dict[str, str] = {}
        self.tags: set[str] = set()
        self.deleted: list[str] = []
        self.force_truncated = False
        self.fallback_exhausted = False
        self.rate_limited = False
        self.unavailable = False
        self.permission_drift = False
        self.tag_collision = False
        self.parent_mismatch_on_update = False
        self.oauth_base_url = "https://github.example.com"
        self.exchanged: list[dict[str, Any]] = []
        self.user_installations_pages: list[dict[str, Any]] = [{"installations": [{"id": 101}], "total_count": 1}]

    def _log(self, method: str, path: str) -> None:
        self.request_log.append({"method": method, "url": f"https://api.github.example.com{path}", "header_names": ["Accept", "Authorization"]})

    def mint_installation_token(self, registration: GitHubAppRegistration, installation_id: int) -> dict[str, Any]:
        self._log("POST", f"/app/installations/{installation_id}/access_tokens")
        if self.rate_limited:
            raise GitHubAppClientError("rate_limited", status_code=429)
        if self.unavailable:
            raise GitHubAppClientError("provider_unavailable", status_code=503)
        permissions = dict(self.permissions.get(registration.registration_id, registration.expected_permissions))
        if self.permission_drift:
            permissions["administration"] = "write"
        return {"token": f"ghs_fixture_{registration.registration_id}", "permissions": permissions, "expires_at": "2026-09-13T10:05:00Z"}

    def get_app_installation(self, registration: GitHubAppRegistration, installation_id: int) -> dict[str, Any]:
        return self.get_installation("app-jwt", installation_id)

    def get_installation(self, token: str, installation_id: int) -> dict[str, Any]:
        self._log("GET", f"/app/installations/{installation_id}")
        if installation_id not in self.installations:
            raise GitHubAppClientError("not_found", status_code=404)
        return self.installations[installation_id]

    def exchange_user_code(
        self,
        registration: GitHubAppRegistration,
        authorization_code: str,
        callback_url: str,
        code_verifier: str,
    ) -> dict[str, str]:
        self.request_log.append(
            {"method": "POST", "url": f"{self.oauth_base_url}/login/oauth/access_token", "header_names": ["Accept"]}
        )
        if not registration.client_id or not registration.client_secret or not code_verifier:
            raise GitHubAppClientError("provider_unavailable")
        self.exchanged.append(
            {
                "client_id": registration.client_id,
                "authorization_code": authorization_code,
                "callback_url": callback_url,
                "code_verifier": code_verifier,
            }
        )
        return {"access_token": "ghu_fixture_user", "refresh_token": "ghr_fixture_refresh"}

    def get_authenticated_user(self, token: str) -> dict[str, Any]:
        self._log("GET", "/user")
        return {"id": 303, "login": "example-user"}

    def list_user_installations(self, token: str, page: int = 1, per_page: int = 100) -> dict[str, Any]:
        self._log("GET", "/user/installations")
        if page < 1 or page > len(self.user_installations_pages):
            return {"installations": [], "total_count": 0}
        return dict(self.user_installations_pages[page - 1])

    def list_installation_repositories(self, token: str, page: int = 1, per_page: int = 30) -> dict[str, Any]:
        self._log("GET", "/installation/repositories")
        return {"repositories": self.repositories, "total_count": len(self.repositories)}

    def get_commit(self, token: str, owner: str, repo: str, ref: str) -> dict[str, Any]:
        self._log("GET", f"/repos/{owner}/{repo}/commits/{ref}")
        if ref not in self.commits:
            raise GitHubAppClientError("not_found", status_code=404)
        return self.commits[ref]

    def get_git_tree(self, token: str, owner: str, repo: str, tree_sha: str, recursive: bool = False) -> dict[str, Any]:
        self._log("GET", f"/repos/{owner}/{repo}/git/trees/{tree_sha}")
        if self.force_truncated and recursive:
            return {"truncated": True, "tree": []}
        if self.fallback_exhausted:
            return {"truncated": True, "tree": []}
        return dict(self.trees[tree_sha])

    def get_git_blob(self, token: str, owner: str, repo: str, blob_sha: str) -> dict[str, Any]:
        self._log("GET", f"/repos/{owner}/{repo}/git/blobs/{blob_sha}")
        return dict(self.blobs[blob_sha])

    def create_organization_repository(self, token: str, org: str, name: str) -> dict[str, Any]:
        self._log("POST", f"/orgs/{org}/repos")
        created = {"id": 909, "name": name, "private": True}
        self.created_repos.append(created)
        return created

    def resolve_user_login_by_email(self, token: str, email: str) -> str:
        self._log("GET", "/search/users")
        return str(self.resolved_logins.get(email.strip().lower(), ""))

    def add_repository_collaborator(
        self,
        token: str,
        owner: str,
        repo_name: str,
        username: str,
        permission: str = "push",
    ) -> bool:
        self._log("PUT", f"/repos/{owner}/{repo_name}/collaborators/{username}")
        self.added_collaborators.append(
            {"owner": owner, "repo_name": repo_name, "username": username, "permission": permission}
        )
        return True

    def create_git_blob(self, token: str, owner: str, repo: str, content_base64: str) -> dict[str, Any]:
        self._log("POST", f"/repos/{owner}/{repo}/git/blobs")
        return {"sha": hashlib.sha1(content_base64.encode("ascii")).hexdigest()}

    def create_git_tree(self, token: str, owner: str, repo: str, tree: list[dict[str, str]]) -> dict[str, Any]:
        self._log("POST", f"/repos/{owner}/{repo}/git/trees")
        return {"sha": "tree-created"}

    def create_git_commit(self, token: str, owner: str, repo: str, message: str, tree_sha: str, parents: list[str]) -> dict[str, Any]:
        self._log("POST", f"/repos/{owner}/{repo}/git/commits")
        sha = "bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb" if message == "baseline" else "cccccccccccccccccccccccccccccccccccccccc"
        return {"sha": sha}

    def create_git_ref(self, token: str, owner: str, repo: str, ref: str, sha: str) -> dict[str, Any]:
        self._log("POST", f"/repos/{owner}/{repo}/git/refs")
        if self.tag_collision and ref.startswith("refs/tags/"):
            raise GitHubAppClientError("conflict", status_code=409)
        self.refs[ref] = sha
        return {"ref": ref, "object": {"sha": sha}}

    def get_git_ref(self, token: str, owner: str, repo: str, ref: str) -> dict[str, Any]:
        self._log("GET", f"/repos/{owner}/{repo}/git/ref/{ref}")
        sha = self.refs.get(f"refs/{ref}", self.refs.get("refs/heads/main", "bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb"))
        return {"object": {"sha": sha}}

    def update_git_ref(self, token: str, owner: str, repo: str, ref: str, sha: str) -> dict[str, Any]:
        self._log("PATCH", f"/repos/{owner}/{repo}/git/refs/{ref}")
        if self.parent_mismatch_on_update:
            raise GitHubAppClientError("unprocessable", status_code=422)
        self.refs[f"refs/{ref}"] = sha
        return {"object": {"sha": sha}}

    def create_git_tag(self, token: str, owner: str, repo: str, tag: str, message: str, object_sha: str) -> dict[str, Any]:
        self._log("POST", f"/repos/{owner}/{repo}/git/tags")
        if tag in self.tags:
            raise GitHubAppClientError("conflict", status_code=409)
        self.tags.add(tag)
        return {"sha": "tag-sha", "tag": tag}

    def delete_repository(self, token: str, owner: str, repo: str) -> None:
        self._log("DELETE", f"/repos/{owner}/{repo}")
        self.deleted.append(f"{owner}/{repo}")


def _sink() -> VaultAgentMemoryCredentialSink:
    return VaultAgentMemoryCredentialSink(
        memory={
            "source-read": GitHubAppRegistration(
                registration_id="source-read",
                app_id="1001",
                private_key_pem="dummy-source-pem",
                expected_permissions={"metadata": "read", "contents": "read"},
                slug="example-source-import",
                client_id="Iv1.example-source",
                client_secret="dummy-source-client-secret",
            ),
            "managed-write": GitHubAppRegistration(
                registration_id="managed-write",
                app_id="2002",
                private_key_pem="dummy-managed-pem",
                expected_permissions={"contents": "write", "administration": "write"},
                organization_allowlist=("example-org",),
            ),
        }
    )


def _service(client: FixtureGitHubAppClient | None = None) -> tuple[GitHubAppService, FixtureGitHubAppClient]:
    fixture_client = client or FixtureGitHubAppClient()
    service = GitHubAppService(client=fixture_client, credential_sink=_sink(), clock=lambda: CLOCK)
    return service, fixture_client


def _grant(operation: str, constraints: dict[str, Any] | None = None, **extra: Any) -> dict[str, Any]:
    now = int(CLOCK.timestamp())
    resource_constraints = dict(constraints or {})
    if operation == "repository.create_private":
        resource_constraints.setdefault("writeCollaboratorEmail", "operator@example.com")
        resource_constraints.setdefault("writeCollaboratorLogin", "octocat")
    payload = {
        "grantId": extra.pop("grantId", f"grant-{operation}-{extra.get('nonce', 'n1')}"),
        "iss": extra.pop("iss", "hape-platform-agent-authorization"),
        "aud": extra.pop("aud", "hape-framework"),
        "sub": extra.pop("sub", "hape-platform-agent-backend"),
        "tenantId": extra.pop("tenantId", "11111111-1111-1111-1111-111111111111"),
        "appId": extra.pop("appId", "33333333-3333-3333-3333-333333333333"),
        "operation": operation,
        "resourceConstraints": resource_constraints,
        "inputDigest": extra.pop("inputDigest", hashlib.sha256(operation.encode("utf-8")).hexdigest()),
        "nonce": extra.pop("nonce", "nonce-1"),
        "iat": extra.pop("iat", now),
        "exp": extra.pop("exp", now + 300),
        "decisionId": extra.pop("decisionId", "decision-1"),
    }
    payload.update(extra)
    return payload


FIXTURE_SETUP_STATE = "ab" * 32
FIXTURE_CALLBACK_URL = "https://app.example.com/github/authorization/callback"
FIXTURE_AUTHORIZATION_CODE = "fixture-authorization-code"
FIXTURE_CODE_VERIFIER = "fixture-code-verifier"


def _source_bindings() -> dict[str, Any]:
    return {
        "hapeAccountId": "11111111-1111-1111-1111-111111111111",
        "browserSessionId": "sess-aaa",
        "returnPath": "/workspace/33333333-3333-3333-3333-333333333333",
        "sourceImportRegistrationId": "source-import",
        "setupState": FIXTURE_SETUP_STATE,
        "installationId": 101,
        "callbackUrl": FIXTURE_CALLBACK_URL,
    }


def _verify_installation(service: GitHubAppService, nonce: str, *, authorization_code: str = FIXTURE_AUTHORIZATION_CODE, installation_id: int = 101) -> dict[str, Any]:
    return service.verify_installation(
        _grant("installation.verify", _source_bindings(), nonce=nonce),
        f"key-{nonce}",
        authorization_code,
        FIXTURE_CODE_VERIFIER,
        installation_id,
        FIXTURE_CALLBACK_URL,
    )


def test_setup_and_verify_installation() -> None:
    service, client = _service()
    setup = service.create_setup_url(_grant("installation.setup_url", _source_bindings(), nonce="s1"), "key-setup")
    assert setup["setupUrl"] == f"https://github.example.com/apps/example-source-import/installations/new?state={FIXTURE_SETUP_STATE}"
    assert "token" not in setup["setupUrl"]
    assert "state" not in setup
    assert setup["safeProviderIds"]["clientId"] == "Iv1.example-source"
    verify = _verify_installation(service, "v1")
    assert verify["status"] == "succeeded"
    assert verify["resourceIds"]["installationId"] == 101
    assert client.exchanged[0]["code_verifier"] == FIXTURE_CODE_VERIFIER
    methods = [item["method"] + " " + item["url"] for item in client.request_log]
    assert methods[0].endswith("/login/oauth/access_token")
    assert any(item.endswith("/user") for item in methods)
    assert any(item.endswith("/user/installations") for item in methods)
    mint_indexes = [index for index, item in enumerate(methods) if item.endswith("/access_tokens")]
    inspect_indexes = [index for index, item in enumerate(methods) if item.endswith("/app/installations/101") and methods[index].startswith("GET ")]
    assert inspect_indexes and mint_indexes and inspect_indexes[0] < mint_indexes[0]
    serialized = str(verify)
    assert "ghu_" not in serialized
    assert "ghr_" not in serialized
    assert FIXTURE_AUTHORIZATION_CODE not in serialized
    assert FIXTURE_CODE_VERIFIER not in serialized


def test_replayed_authorization_code_is_denied() -> None:
    service, _client = _service()
    _verify_installation(service, "v-replay-1")
    with pytest.raises(GitHubAppError) as replayed:
        _verify_installation(service, "v-replay-2")
    assert replayed.value.code == "replay_denied"


def test_missing_setup_state_is_denied() -> None:
    service, _client = _service()
    constraints = _source_bindings()
    constraints.pop("setupState")
    with pytest.raises(GitHubAppError) as exc:
        service.create_setup_url(_grant("installation.setup_url", constraints, nonce="s-missing"), "key-missing-state")
    assert exc.value.code == "policy_denied"


def test_spoofed_installation_id_is_not_found() -> None:
    service, client = _service()
    client.user_installations_pages = [{"installations": [{"id": 999}], "total_count": 1}]
    with pytest.raises(GitHubAppError) as exc:
        _verify_installation(service, "v-spoof")
    assert exc.value.code == "not_found"
    assert not any(item["url"].endswith("/access_tokens") for item in client.request_log)


def test_paginated_user_installations_match_exact_id() -> None:
    service, client = _service()
    client.user_installations_pages = [
        {"installations": [{"id": 200 + index} for index in range(100)], "total_count": 101},
        {"installations": [{"id": 101}], "total_count": 101},
    ]
    verify = _verify_installation(service, "v-page")
    assert verify["status"] == "succeeded"
    assert sum(1 for item in client.request_log if item["url"].endswith("/user/installations")) == 2


def test_wrong_registration_is_not_found() -> None:
    service, _client = _service()
    managed = _source_bindings()
    managed["sourceImportRegistrationId"] = "managed-repositories"
    with pytest.raises(GitHubAppError) as registration:
        service.verify_installation(
            _grant("installation.verify", managed, nonce="v5"),
            "key-reg",
            FIXTURE_AUTHORIZATION_CODE,
            FIXTURE_CODE_VERIFIER,
            101,
            FIXTURE_CALLBACK_URL,
        )
    assert registration.value.code == "not_found"


def test_discover_hides_non_enumerating_and_fail_closed_repos() -> None:
    service, _client = _service()
    receipt = service.discover_repositories(_grant("repository.discover", {"installationId": 101}, nonce="d1"), "key-discover")
    names = [item["name"] for item in receipt["repositories"]]
    assert names == ["source-repo"]
    with pytest.raises(GitHubAppError) as hidden:
        service.discover_repositories(
            _grant("repository.discover", {"installationId": 101, "repositoryDatabaseId": 203}, nonce="d2", inputDigest="hidden"),
            "key-hidden",
        )
    assert hidden.value.code == "not_found"


def test_revision_and_snapshot_read() -> None:
    service, _client = _service()
    revision = service.resolve_revision(
        _grant(
            "revision.resolve",
            {"installationId": 101, "owner": "example-user", "repository": "source-repo", "ref": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa", "repositoryDatabaseId": 202},
            nonce="r1",
        ),
        "key-rev",
    )
    assert revision["outputDigest"] == "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"
    snapshot = service.read_snapshot(
        _grant(
            "snapshot.read",
            {"installationId": 101, "owner": "example-user", "repository": "source-repo", "commitSha": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"},
            nonce="snap1",
        ),
        "key-snap",
    )
    assert snapshot["aggregateDigest"] == "efec814a4b84dba35fe99ef6b3515ed5dbeca273835743122cc73c76bdb7f767"
    assert "bytes" not in snapshot
    assert "source_body" not in snapshot


def test_truncated_tree_fallback_and_unresolved() -> None:
    client = FixtureGitHubAppClient()
    client.force_truncated = True
    service, _client = _service(client)
    snapshot = service.read_snapshot(
        _grant(
            "snapshot.read",
            {"installationId": 101, "owner": "example-user", "repository": "source-repo", "commitSha": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"},
            nonce="snap2",
        ),
        "key-fallback",
    )
    assert snapshot["aggregateDigest"] == "efec814a4b84dba35fe99ef6b3515ed5dbeca273835743122cc73c76bdb7f767"
    exhausted = FixtureGitHubAppClient()
    exhausted.fallback_exhausted = True
    failing, _client = _service(exhausted)
    with pytest.raises(GitHubAppError) as exc:
        failing.read_snapshot(
            _grant(
                "snapshot.read",
                {"installationId": 101, "owner": "example-user", "repository": "source-repo", "commitSha": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"},
                nonce="snap3",
            ),
            "key-truncated",
        )
    assert exc.value.code == "provider_unavailable"


def test_managed_copy_baseline_artifact_tag_and_dispose() -> None:
    service, client = _service()
    snapshot = service.read_snapshot(
        _grant(
            "snapshot.read",
            {"installationId": 101, "owner": "example-user", "repository": "source-repo", "commitSha": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"},
            nonce="snap4",
        ),
        "key-snap-copy",
    )
    created = service.create_private_repository(
        _grant(
            "repository.create_private",
            {"installationId": 9091, "hapeOrganizationId": "example-org", "sourceSnapshotDigest": snapshot["aggregateDigest"]},
            nonce="c1",
        ),
        "key-create",
    )
    repository_id = created["safeProviderIds"]["repositoryId"]
    assert client.added_collaborators[-1] == {
        "owner": "example-org",
        "repo_name": created["safeProviderIds"]["repositoryName"],
        "username": "octocat",
        "permission": "push",
    }
    baseline = service.publish_baseline(_grant("commit.publish_baseline", {"repositoryId": repository_id}, nonce="b1"), "key-base")
    assert baseline["safeProviderIds"]["commitSha"] == "bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb"
    artifact_files = [
        {"path": "README.md", "mode": "100644", "bytes": b"# Example\n"},
        {"path": "src/hello.txt", "mode": "100644", "bytes": b"hello\n"},
    ]
    digest = service.admit_local_files(artifact_files)[1]
    artifact = service.publish_artifact(
        _grant(
            "commit.publish_artifact",
            {"repositoryId": repository_id, "expectedParentSha": "bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb", "reviewDigest": digest},
            nonce="a1",
            expectedParent="bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb",
            runId="55555555-5555-5555-5555-555555555555",
            reviewId="66666666-6666-6666-6666-666666666666",
        ),
        "key-art",
        artifact_files,
        "content_bearing",
    )
    assert artifact["safeProviderIds"]["commitSha"] == "cccccccccccccccccccccccccccccccccccccccc"
    tagged = service.publish_annotated_tag(
        _grant(
            "tag.publish_annotated",
            {"repositoryId": repository_id, "opaqueSubjectId": "55555555555555555555555555555555", "commitSha": "cccccccccccccccccccccccccccccccccccccccc"},
            nonce="t1",
            runId="55555555-5555-5555-5555-555555555555",
            reviewId="66666666-6666-6666-6666-666666666666",
        ),
        "key-tag",
    )
    assert tagged["safeProviderIds"]["tag"].startswith("hape-pub-55555555555555555555555555555555-")
    disposed = service.dispose_repository(_grant("repository.dispose", {"repositoryId": repository_id}, nonce="z1"), "key-dispose")
    assert disposed["status"] == "completed"
    assert client.deleted
    assert all("ghs_" not in item["url"] for item in client.request_log)


def test_organization_mismatch_and_plan_blueprint_and_parent_mismatch() -> None:
    service, _client = _service()
    snapshot = service.read_snapshot(
        _grant(
            "snapshot.read",
            {"installationId": 101, "owner": "example-user", "repository": "source-repo", "commitSha": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"},
            nonce="snap5",
        ),
        "key-snap-neg",
    )
    with pytest.raises(GitHubAppError) as org:
        service.create_private_repository(
            _grant(
                "repository.create_private",
                {"installationId": 9091, "hapeOrganizationId": "other-org", "sourceSnapshotDigest": snapshot["aggregateDigest"]},
                nonce="c-bad",
            ),
            "key-org",
        )
    assert org.value.code == "organization_mismatch"
    created = service.create_private_repository(
        _grant(
            "repository.create_private",
            {"installationId": 9091, "hapeOrganizationId": "example-org", "sourceSnapshotDigest": snapshot["aggregateDigest"]},
            nonce="c2",
        ),
        "key-create-2",
    )
    repository_id = created["safeProviderIds"]["repositoryId"]
    service.publish_baseline(_grant("commit.publish_baseline", {"repositoryId": repository_id}, nonce="b2"), "key-base-2")
    with pytest.raises(GitHubAppError) as blueprint:
        service.publish_artifact(
            _grant(
                "commit.publish_artifact",
                {"repositoryId": repository_id, "expectedParentSha": "bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb", "reviewDigest": "0" * 64},
                nonce="a-bad",
                expectedParent="bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb",
                runId="55555555-5555-5555-5555-555555555555",
                reviewId="66666666-6666-6666-6666-666666666666",
            ),
            "key-blueprint",
            [],
            "plan_blueprint_only",
        )
    assert blueprint.value.code == "digest_mismatch"
    with pytest.raises(GitHubAppError) as parent:
        service.publish_artifact(
            _grant(
                "commit.publish_artifact",
                {"repositoryId": repository_id, "expectedParentSha": "dddddddddddddddddddddddddddddddddddddddd", "reviewDigest": snapshot["aggregateDigest"]},
                nonce="a-parent",
                expectedParent="dddddddddddddddddddddddddddddddddddddddd",
                runId="55555555-5555-5555-5555-555555555555",
                reviewId="66666666-6666-6666-6666-666666666666",
            ),
            "key-parent",
            [{"path": "README.md", "mode": "100644", "bytes": b"# Example\n"}],
            "content_bearing",
        )
    assert parent.value.code == "parent_mismatch"


def test_idempotency_replay_and_conflict() -> None:
    service, _client = _service()
    first = service.discover_repositories(_grant("repository.discover", {"installationId": 101}, nonce="id1", inputDigest="same"), "same-key")
    second = service.discover_repositories(_grant("repository.discover", {"installationId": 101}, nonce="id2", inputDigest="same"), "same-key")
    assert second["receiptId"] == first["receiptId"]
    with pytest.raises(GitHubAppError) as exc:
        service.discover_repositories(_grant("repository.discover", {"installationId": 101}, nonce="id3", inputDigest="other"), "same-key")
    assert exc.value.code == "conflict"


def test_grant_expiry_replay_and_legacy_permission_drift() -> None:
    service, client = _service()
    expired = _grant("repository.discover", {"installationId": 101}, nonce="g-exp", iat=int(CLOCK.timestamp()) - 200, exp=int(CLOCK.timestamp()) - 1)
    with pytest.raises(GitHubAppError) as grant_expired:
        service.discover_repositories(expired, "key-grant-exp")
    assert grant_expired.value.code == "grant_expired"
    first = _grant("repository.discover", {"installationId": 101}, nonce="g-replay", grantId="reuse-me")
    service.discover_repositories(first, "key-grant-1")
    with pytest.raises(GitHubAppError) as replayed:
        service.discover_repositories(first, "key-grant-2")
    assert replayed.value.code == "grant_replayed"
    drifted, drift_client = _service()
    drift_client.permission_drift = True
    with pytest.raises(GitHubAppError) as drift:
        drifted.discover_repositories(_grant("repository.discover", {"installationId": 101}, nonce="g-drift"), "key-drift")
    assert drift.value.code == "policy_denied"


def test_legal_hold_and_tag_collision_and_rate_limit() -> None:
    service, client = _service()
    snapshot = service.read_snapshot(
        _grant(
            "snapshot.read",
            {"installationId": 101, "owner": "example-user", "repository": "source-repo", "commitSha": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"},
            nonce="snap6",
        ),
        "key-snap-6",
    )
    created = service.create_private_repository(
        _grant(
            "repository.create_private",
            {"installationId": 9091, "hapeOrganizationId": "example-org", "sourceSnapshotDigest": snapshot["aggregateDigest"]},
            nonce="c3",
        ),
        "key-create-3",
    )
    repository_id = created["safeProviderIds"]["repositoryId"]
    with pytest.raises(GitHubAppError) as hold:
        service.dispose_repository(_grant("repository.dispose", {"repositoryId": repository_id, "legalHold": True}, nonce="hold"), "key-hold")
    assert hold.value.code == "legal_hold_unsupported"
    client.tag_collision = True
    service.publish_baseline(_grant("commit.publish_baseline", {"repositoryId": repository_id}, nonce="b3"), "key-base-3")
    with pytest.raises(GitHubAppError) as collision:
        service.publish_annotated_tag(
            _grant(
                "tag.publish_annotated",
                {"repositoryId": repository_id, "opaqueSubjectId": "55555555555555555555555555555555"},
                nonce="t-bad",
                runId="55555555-5555-5555-5555-555555555555",
                reviewId="66666666-6666-6666-6666-666666666666",
            ),
            "key-tag-bad",
        )
    assert collision.value.code == "conflict"
    limited_service, limited_client = _service()
    limited_client.rate_limited = True
    with pytest.raises(GitHubAppError) as limited:
        limited_service.discover_repositories(_grant("repository.discover", {"installationId": 101}, nonce="rate"), "key-rate")
    assert limited.value.code == "rate_limited"


def test_create_private_fails_closed_without_write_collaborator() -> None:
    service, _client = _service()
    snapshot = service.read_snapshot(
        _grant(
            "snapshot.read",
            {"installationId": 101, "owner": "example-user", "repository": "source-repo", "commitSha": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"},
            nonce="snap-write",
        ),
        "key-snap-write",
    )
    with pytest.raises(GitHubAppError) as missing:
        service.create_private_repository(
            _grant(
                "repository.create_private",
                {
                    "installationId": 9091,
                    "hapeOrganizationId": "example-org",
                    "sourceSnapshotDigest": snapshot["aggregateDigest"],
                    "writeCollaboratorEmail": "",
                    "writeCollaboratorLogin": "",
                },
                nonce="c-missing",
            ),
            "key-missing-write",
        )
    assert missing.value.code == "write_collaborator_required"


def test_receipts_are_redacted_and_service_does_not_use_subprocess() -> None:
    import services.github_app_service as module

    service, _client = _service()
    receipt = service.discover_repositories(_grant("repository.discover", {"installationId": 101}, nonce="redact"), "key-redact")
    serialized = str(receipt)
    assert "ghs_" not in serialized
    assert "BEGIN" not in serialized
    assert "private_key" not in serialized
    fetched = service.get_receipt(_grant("receipt.get", {}, nonce="get-r", tenantId=receipt["subject"]), receipt["receiptId"])
    assert fetched["receiptId"] == receipt["receiptId"]
    assert "subprocess" not in module.__dict__


def test_empty_vault_memory_fails_closed() -> None:
    service = GitHubAppService(client=FixtureGitHubAppClient(), credential_sink=VaultAgentMemoryCredentialSink(), clock=lambda: CLOCK)
    with pytest.raises(GitHubAppError) as exc:
        service.discover_repositories(_grant("repository.discover", {"installationId": 101}, nonce="empty"), "key-empty")
    assert exc.value.code == "provider_unavailable"


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__]))
