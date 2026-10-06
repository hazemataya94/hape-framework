from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import secrets
from threading import Lock
from typing import Any


@dataclass
class TokenRecord:
    token_id: str
    name: str
    token_hash: str
    created_at: str
    revoked: bool = False
    credential_role: str | None = None
    allowed_operations: list[str] | None = None
    iss: str | None = None
    aud: str | None = None
    sub: str | None = None
    jti: str | None = None
    iat: int | None = None
    exp: int | None = None


class ApiTokenService:
    DEFAULT_TOKEN_PREFIX = "hape_"
    PRODUCT_CALLER_TTL_SECONDS = 7 * 24 * 3600

    def __init__(self, store_file_path: str) -> None:
        self.store_file_path = Path(store_file_path).expanduser().resolve()
        self._lock = Lock()

    @staticmethod
    def _hash_token(token: str) -> str:
        return hashlib.sha256(token.encode("utf-8")).hexdigest()

    def _ensure_store_parent(self) -> None:
        self.store_file_path.parent.mkdir(parents=True, exist_ok=True)

    def _read_store(self) -> dict[str, Any]:
        if not self.store_file_path.exists():
            return {"tokens": []}
        payload = json.loads(self.store_file_path.read_text(encoding="utf-8"))
        if not isinstance(payload, dict):
            return {"tokens": []}
        tokens = payload.get("tokens", [])
        if not isinstance(tokens, list):
            return {"tokens": []}
        return {"tokens": tokens}

    def _write_store(self, payload: dict[str, Any]) -> None:
        self._ensure_store_parent()
        self.store_file_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    def create_token(
        self,
        name: str,
        *,
        credential_role: str | None = None,
        allowed_operations: list[str] | None = None,
        iss: str | None = None,
        aud: str | None = None,
        sub: str | None = None,
        exp_seconds: int | None = None,
    ) -> dict[str, str]:
        normalized_name = name.strip() or "default"
        raw_token = f"{self.DEFAULT_TOKEN_PREFIX}{secrets.token_urlsafe(32)}"
        issued_at = datetime.now(timezone.utc)
        token_record: dict[str, Any] = {
            "token_id": secrets.token_hex(8),
            "name": normalized_name,
            "token_hash": self._hash_token(raw_token),
            "created_at": issued_at.isoformat(),
            "revoked": False,
        }
        if credential_role:
            token_record["credential_role"] = credential_role
            token_record["allowed_operations"] = list(allowed_operations or [])
            token_record["iss"] = iss or "hape-platform-agent-backend"
            token_record["aud"] = aud or "hape-framework"
            token_record["sub"] = sub or "hape-platform-agent-backend"
            token_record["jti"] = secrets.token_hex(16)
            token_record["iat"] = int(issued_at.timestamp())
            token_record["exp"] = int(issued_at.timestamp()) + int(exp_seconds or self.PRODUCT_CALLER_TTL_SECONDS)
            if token_record["exp"] <= token_record["iat"]:
                raise ValueError("Product caller tokens must expire.")
        with self._lock:
            payload = self._read_store()
            payload["tokens"].append(token_record)
            self._write_store(payload)
        created: dict[str, str] = {
            "token": raw_token,
            "token_id": token_record["token_id"],
            "name": token_record["name"],
            "created_at": token_record["created_at"],
        }
        if credential_role:
            created["credential_role"] = str(token_record["credential_role"])
            created["jti"] = str(token_record["jti"])
        return created

    def list_tokens(self) -> list[dict[str, str | bool]]:
        with self._lock:
            payload = self._read_store()
        result: list[dict[str, str | bool]] = []
        for token_item in payload.get("tokens", []):
            if not isinstance(token_item, dict):
                continue
            result.append(
                {
                    "token_id": str(token_item.get("token_id", "")),
                    "name": str(token_item.get("name", "")),
                    "created_at": str(token_item.get("created_at", "")),
                    "revoked": bool(token_item.get("revoked", False)),
                }
            )
        return result

    def revoke_token(self, token_id: str) -> bool:
        revoked = False
        with self._lock:
            payload = self._read_store()
            tokens = payload.get("tokens", [])
            for token_item in tokens:
                if not isinstance(token_item, dict):
                    continue
                if str(token_item.get("token_id", "")) != token_id:
                    continue
                token_item["revoked"] = True
                revoked = True
            if revoked:
                self._write_store(payload)
        return revoked

    def validate_token(self, token: str) -> dict[str, Any] | None:
        token_hash = self._hash_token(token)
        now_ts = int(datetime.now(timezone.utc).timestamp())
        with self._lock:
            payload = self._read_store()
        for token_item in payload.get("tokens", []):
            if not isinstance(token_item, dict):
                continue
            if bool(token_item.get("revoked", False)):
                continue
            if str(token_item.get("token_hash", "")) != token_hash:
                continue
            exp_value = token_item.get("exp")
            if exp_value not in (None, "") and int(exp_value) <= now_ts:
                return None
            allowed_operations = token_item.get("allowed_operations") or []
            if not isinstance(allowed_operations, list):
                allowed_operations = []
            return {
                "token_id": str(token_item.get("token_id", "")),
                "name": str(token_item.get("name", "")),
                "token_hash": token_hash,
                "revoked": False,
                "credential_role": token_item.get("credential_role"),
                "allowed_operations": [str(item) for item in allowed_operations],
                "iss": token_item.get("iss"),
                "aud": token_item.get("aud"),
                "sub": token_item.get("sub"),
                "jti": token_item.get("jti"),
                "iat": token_item.get("iat"),
                "exp": token_item.get("exp"),
            }
        return None
