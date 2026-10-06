from __future__ import annotations

import hashlib
import json
import unicodedata
from typing import Any


def normalize_text(value: str) -> str:
    return unicodedata.normalize("NFC", value)


def canonicalize(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(key): canonicalize(value[key]) for key in sorted(value)}
    if isinstance(value, list):
        return [canonicalize(item) for item in value]
    if isinstance(value, str):
        return normalize_text(value)
    if isinstance(value, bool) or value is None or isinstance(value, int):
        return value
    if isinstance(value, float):
        raise ValueError("floating-point values are not allowed")
    return value


def canonical_json(value: Any) -> str:
    return json.dumps(canonicalize(value), ensure_ascii=False, separators=(",", ":"), sort_keys=True)


def sha256_hex(value: str | bytes) -> str:
    payload = value if isinstance(value, bytes) else value.encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def request_digest(payload: dict[str, Any]) -> str:
    return sha256_hex(canonical_json(payload))


if __name__ == "__main__":
    print(request_digest({"operation": "managed_destination.status"}))
