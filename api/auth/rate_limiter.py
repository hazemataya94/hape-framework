from __future__ import annotations

import time
from threading import Lock


class TokenRateLimiter:
    WINDOW_SECONDS = 60

    def __init__(self, limit_per_minute: int) -> None:
        self.limit_per_minute = limit_per_minute
        self._token_hits: dict[str, list[float]] = {}
        self._lock = Lock()

    def allow(self, token_hash: str) -> tuple[bool, int]:
        now = time.time()
        window_start = now - self.WINDOW_SECONDS
        with self._lock:
            hits = self._token_hits.get(token_hash, [])
            fresh_hits = [hit for hit in hits if hit >= window_start]
            if len(fresh_hits) >= self.limit_per_minute:
                retry_after = int(max(1, self.WINDOW_SECONDS - (now - fresh_hits[0])))
                self._token_hits[token_hash] = fresh_hits
                return False, retry_after
            fresh_hits.append(now)
            self._token_hits[token_hash] = fresh_hits
            return True, 0
