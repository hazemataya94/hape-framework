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


class ApiTokenService:
    DEFAULT_TOKEN_PREFIX = "hape_"

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

    def create_token(self, name: str) -> dict[str, str]:
        normalized_name = name.strip() or "default"
        raw_token = f"{self.DEFAULT_TOKEN_PREFIX}{secrets.token_urlsafe(32)}"
        token_record = {
            "token_id": secrets.token_hex(8),
            "name": normalized_name,
            "token_hash": self._hash_token(raw_token),
            "created_at": datetime.now(timezone.utc).isoformat(),
            "revoked": False,
        }
        with self._lock:
            payload = self._read_store()
            payload["tokens"].append(token_record)
            self._write_store(payload)
        return {
            "token": raw_token,
            "token_id": token_record["token_id"],
            "name": token_record["name"],
            "created_at": token_record["created_at"],
        }

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

    def validate_token(self, token: str) -> dict[str, str] | None:
        token_hash = self._hash_token(token)
        with self._lock:
            payload = self._read_store()
        for token_item in payload.get("tokens", []):
            if not isinstance(token_item, dict):
                continue
            if bool(token_item.get("revoked", False)):
                continue
            if str(token_item.get("token_hash", "")) != token_hash:
                continue
            return {
                "token_id": str(token_item.get("token_id", "")),
                "name": str(token_item.get("name", "")),
                "token_hash": token_hash,
            }
        return None
