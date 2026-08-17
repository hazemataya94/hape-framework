from __future__ import annotations

import html
import json
import re
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.parse import urlparse, urlunparse

import requests

from core.logging import LocalLogging


class LinkedInClient:
    DEFAULT_TIMEOUT_SECONDS = 30
    DEFAULT_MAX_RETRIES = 2
    DEFAULT_RETRY_BACKOFF_SECONDS = 1.0
    DEFAULT_REQUEST_DELAY_SECONDS = 0.75
    DEFAULT_USER_AGENT = (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/131.0.0.0 Safari/537.36"
    )
    PROFILE_PATH_RE = re.compile(r"^/in/(?P<slug>[A-Za-z0-9_-]+)/?$")
    AUTHWALL_MARKERS = (
        "authwall",
        "auth_wall",
        "auth_wall_desktop",
        "join linkedin",
        "sign up | linkedin",
        "session_redirect",
    )
    ACTIVITY_URN_RE = re.compile(r"urn:li:(?:activity|ugcPost|share):(\d+)")
    ACTIVITY_IN_PATH_RE = re.compile(r"activity-(\d+)", re.IGNORECASE)
    COMMENTARY_RE = re.compile(
        r'"commentary"\s*:\s*\{.*?"text"\s*:\s*"(?P<text>(?:\\.|[^"\\])*)"',
        re.DOTALL,
    )
    COMMENTARY_DOM_RE = re.compile(
        r'update-components-update-v2__commentary[^>]*>.*?class="break-words[^"]*"[^>]*>(?P<body>.*?)</span>\s*</div>',
        re.IGNORECASE | re.DOTALL,
    )
    POSTED_AGO_RE = re.compile(
        r"(?P<ago>\d+\s*[smhdw]|just\s+now)\s*•",
        re.IGNORECASE,
    )
    LOCAL_IMG_SRC_RE = re.compile(
        r'src=["\'](?P<src>(?:\./)?(?P<rel>[^"\']+_files/[^"\']+))["\']',
        re.IGNORECASE,
    )
    UPDATE_IMAGE_BLOCK_RE = re.compile(
        r"update-components-image(?P<body>[\s\S]{0,4000}?)</button>",
        re.IGNORECASE,
    )
    IMPRESSIONS_RE = re.compile(
        r"<strong>\s*(?P<count>[\d,]+)\s+impressions?\s*</strong>",
        re.IGNORECASE,
    )
    REACTIONS_COUNT_RE = re.compile(
        r"social-details-social-counts__reactions-count[^>]*>\s*(?P<count>[\d,]+)",
        re.IGNORECASE,
    )
    SOCIAL_PROOF_COUNT_RE = re.compile(
        r"social-details-social-counts__social-proof-container[^>]*>\s*(?P<count>[\d,]+)",
        re.IGNORECASE,
    )
    REACTIONS_ARIA_RE = re.compile(
        r'aria-label="(?P<count>\d+)\s+reactions?"',
        re.IGNORECASE,
    )
    REACTIONS_OTHERS_ARIA_RE = re.compile(
        r'aria-label="[^"]*?and (?P<count>\d+) others"',
        re.IGNORECASE,
    )
    COMMENTS_ARIA_RE = re.compile(
        r'aria-label="(?P<count>\d+)\s+comments? on[^"]*"',
        re.IGNORECASE,
    )
    REPOSTS_ARIA_RE = re.compile(
        r'aria-label="(?P<count>\d+)\s+reposts? of[^"]*"',
        re.IGNORECASE,
    )
    TITLE_MAX_LENGTH = 90
    MIN_LOCAL_MEDIA_BYTES = 5000
    SHARED_ASSET_MAX_OCCURRENCES = 8

    EMBEDDED_JSON_RE = re.compile(
        r'<script[^>]+type=["\']application/(?:ld\+json|json)["\'][^>]*>(?P<body>.*?)</script>',
        re.IGNORECASE | re.DOTALL,
    )
    META_DESCRIPTION_RE = re.compile(
        r'<meta[^>]+(?:name|property)=["\'](?:og:description|description)["\'][^>]+content=["\'](?P<content>[^"\']+)["\']',
        re.IGNORECASE,
    )
    ACTIVITY_HREF_RE = re.compile(
        r'href=["\'](?P<url>https?://(?:www\.)?linkedin\.com/(?:feed/update/[^"\']+|posts/[^"\']+|pulse/[^"\']+))["\']',
        re.IGNORECASE,
    )

    def __init__(
        self,
        timeout_seconds: float = DEFAULT_TIMEOUT_SECONDS,
        max_retries: int = DEFAULT_MAX_RETRIES,
        retry_backoff_seconds: float = DEFAULT_RETRY_BACKOFF_SECONDS,
        request_delay_seconds: float = DEFAULT_REQUEST_DELAY_SECONDS,
        user_agent: str = DEFAULT_USER_AGENT,
        session: requests.Session | None = None,
    ) -> None:
        self.logger = LocalLogging.get_logger("hape.linkedin_client")
        self.timeout_seconds = timeout_seconds
        self.max_retries = max_retries
        self.retry_backoff_seconds = retry_backoff_seconds
        self.request_delay_seconds = request_delay_seconds
        self.user_agent = user_agent
        self.session = session or requests.Session()
        self.session.headers.update(
            {
                "User-Agent": self.user_agent,
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                "Accept-Language": "en-US,en;q=0.9",
            }
        )

    def _normalize_profile_url(self, profile_url: str) -> tuple[str, str]:
        raw = (profile_url or "").strip()
        if not raw:
            raise ValueError("profile_url_required")
        parsed = urlparse(raw)
        scheme = parsed.scheme.lower() if parsed.scheme else "https"
        if scheme not in {"http", "https"}:
            raise ValueError("profile_url_invalid")
        netloc = (parsed.netloc or "").lower()
        if netloc.startswith("www."):
            host = netloc
        elif netloc.endswith("linkedin.com"):
            host = "www.linkedin.com"
        else:
            raise ValueError("profile_url_invalid")
        if host not in {"www.linkedin.com", "linkedin.com"}:
            raise ValueError("profile_url_invalid")
        host = "www.linkedin.com"
        match = self.PROFILE_PATH_RE.match(parsed.path or "")
        if not match:
            raise ValueError("profile_url_invalid")
        slug = match.group("slug")
        normalized = urlunparse(("https", host, f"/in/{slug}/", "", "", ""))
        return normalized, slug

    def _is_retryable_status_code(self, status_code: int) -> bool:
        return status_code == 429 or 500 <= status_code <= 599

    def _looks_like_authwall(self, html_text: str, final_url: str) -> bool:
        lowered = (html_text or "").lower()
        final = (final_url or "").lower()
        if "authwall" in final or "/checkpoint/" in final or "/login" in final:
            return True
        return any(marker in lowered for marker in self.AUTHWALL_MARKERS)

    def _unescape_json_string(self, value: str) -> str:
        try:
            return json.loads(f'"{value}"')
        except json.JSONDecodeError:
            return html.unescape(value.replace("\\n", "\n").replace('\\"', '"'))

    def _fetch_html(self, url: str) -> tuple[str, str, int]:
        last_error: Exception | None = None
        for attempt in range(1, self.max_retries + 2):
            try:
                if attempt > 1 and self.request_delay_seconds > 0:
                    time.sleep(self.retry_backoff_seconds * (2 ** (attempt - 2)))
                elif self.request_delay_seconds > 0:
                    time.sleep(self.request_delay_seconds)
                response = self.session.get(url, timeout=self.timeout_seconds, allow_redirects=True)
                status_code = response.status_code
                if status_code == 999 or self._looks_like_authwall(response.text, str(response.url)):
                    return response.text, str(response.url), status_code
                if self._is_retryable_status_code(status_code) and attempt <= self.max_retries + 1:
                    self.logger.warning(f"retryable LinkedIn status={status_code} attempt={attempt} url={url}")
                    continue
                response.raise_for_status()
                return response.text, str(response.url), status_code
            except requests.RequestException as exc:
                last_error = exc
                self.logger.warning(f"LinkedIn fetch failed attempt={attempt} url={url} error={exc}")
                if attempt > self.max_retries + 1:
                    break
        if last_error is not None:
            raise last_error
        raise RuntimeError(f"Failed to fetch LinkedIn URL: {url}")

    def _empty_post(self, post_id: str, url: str | None, fetched_at: str) -> dict[str, Any]:
        return {
            "id": post_id,
            "url": url,
            "title": "",
            "created_at": None,
            "posted_ago": None,
            "text": "",
            "media_urls": [],
            "media_local_paths": [],
            "media_paths": [],
            "stats": {
                "impressions": None,
                "reactions": None,
                "comments": None,
                "reposts": None,
                "engagements": None,
            },
            "source": "public_html",
            "fetched_at": fetched_at,
        }

    def _activity_id_from_url(self, url: str) -> str | None:
        urn_match = self.ACTIVITY_URN_RE.search(url)
        if urn_match:
            return urn_match.group(1)
        path_match = self.ACTIVITY_IN_PATH_RE.search(url)
        if path_match:
            return path_match.group(1)
        return None

    def _upsert_post(
        self,
        posts_by_id: dict[str, dict[str, Any]],
        post_id: str,
        fetched_at: str,
        url: str | None = None,
        text: str | None = None,
        created_at: Any = None,
        title: str | None = None,
        posted_ago: str | None = None,
        media_local_paths: list[str] | None = None,
        media_urls: list[str] | None = None,
    ) -> None:
        existing = posts_by_id.get(post_id)
        if existing is None:
            posts_by_id[post_id] = self._empty_post(post_id, url, fetched_at)
            existing = posts_by_id[post_id]
        if url and not existing.get("url"):
            existing["url"] = url
        if text and not existing.get("text"):
            existing["text"] = text
        if created_at and not existing.get("created_at"):
            existing["created_at"] = created_at
        if title and not existing.get("title"):
            existing["title"] = title
        if posted_ago and not existing.get("posted_ago"):
            existing["posted_ago"] = posted_ago
        if media_local_paths:
            merged = list(existing.get("media_local_paths") or [])
            for path_value in media_local_paths:
                if path_value not in merged:
                    merged.append(path_value)
            existing["media_local_paths"] = merged
        if media_urls:
            merged_urls = list(existing.get("media_urls") or [])
            for media_url in media_urls:
                if media_url not in merged_urls:
                    merged_urls.append(media_url)
            existing["media_urls"] = merged_urls

    def _html_to_plain_text(self, html_fragment: str) -> str:
        text = html_fragment or ""
        text = re.sub(r"<br\s*/?>", "\n", text, flags=re.IGNORECASE)
        text = re.sub(r"</p\s*>", "\n", text, flags=re.IGNORECASE)
        text = re.sub(r"<a\b[^>]*>", "", text, flags=re.IGNORECASE)
        text = re.sub(r"</a>", "", text, flags=re.IGNORECASE)
        text = re.sub(r"<!---->", "", text)
        text = re.sub(r"<[^>]+>", "", text)
        text = html.unescape(text)
        text = re.sub(r"[ \t]+\n", "\n", text)
        text = re.sub(r"\n{3,}", "\n\n", text)
        return text.strip()

    def _title_from_text(self, text: str) -> str:
        normalized = (text or "").strip()
        if not normalized:
            return ""
        first_line = next((line.strip() for line in normalized.splitlines() if line.strip()), "")
        if not first_line:
            return ""
        if len(first_line) <= self.TITLE_MAX_LENGTH:
            return first_line
        clipped = first_line[: self.TITLE_MAX_LENGTH].rsplit(" ", 1)[0].strip()
        return f"{clipped}..." if clipped else first_line[: self.TITLE_MAX_LENGTH]

    def _extract_commentary_dom_texts(self, html_text: str) -> list[str]:
        texts: list[str] = []
        for match in self.COMMENTARY_DOM_RE.finditer(html_text or ""):
            plain = self._html_to_plain_text(match.group("body"))
            if plain:
                texts.append(plain)
        return texts

    def _detect_image_extension(self, path: Path) -> str | None:
        try:
            header = path.read_bytes()[:16]
        except OSError:
            return None
        if header.startswith(b"\xff\xd8\xff"):
            return "jpg"
        if header.startswith(b"\x89PNG\r\n\x1a\n"):
            return "png"
        if header.startswith(b"GIF87a") or header.startswith(b"GIF89a"):
            return "gif"
        if header.startswith(b"RIFF") and header[8:12] == b"WEBP":
            return "webp"
        return None

    def _shared_local_asset_names(self, html_text: str) -> set[str]:
        counts: dict[str, int] = {}
        for match in self.LOCAL_IMG_SRC_RE.finditer(html_text or ""):
            name = Path(match.group("rel")).name
            counts[name] = counts.get(name, 0) + 1
        return {name for name, count in counts.items() if count > self.SHARED_ASSET_MAX_OCCURRENCES}

    def _extract_local_media_from_chunk(self, chunk: str, shared_asset_names: set[str]) -> list[str]:
        media_paths: list[str] = []
        for block in self.UPDATE_IMAGE_BLOCK_RE.finditer(chunk or ""):
            for match in self.LOCAL_IMG_SRC_RE.finditer(block.group("body")):
                rel = match.group("rel").replace("\\", "/")
                name = Path(rel).name
                if name in shared_asset_names:
                    continue
                if rel in media_paths:
                    continue
                media_paths.append(rel)
        return media_paths

    def _extract_remote_media_from_chunk(self, chunk: str) -> list[str]:
        urls: list[str] = []
        for match in re.finditer(r"https://media\.licdn\.com/dms/image/[^\"'\s<>]+", chunk or "", re.IGNORECASE):
            url = html.unescape(match.group(0))
            lowered = url.lower()
            if "profile-displayphoto" in lowered or "profile-displaybackground" in lowered:
                continue
            if "feedshare" not in lowered and "videocover" not in lowered:
                continue
            if url not in urls:
                urls.append(url)
        return urls

    def _created_at_from_activity_id(self, activity_id: str) -> str | None:
        try:
            snowflake = int(str(activity_id).strip())
        except (TypeError, ValueError):
            return None
        if snowflake <= 0:
            return None
        # LinkedIn activity IDs encode Unix epoch milliseconds in the high bits.
        timestamp_ms = snowflake >> 22
        try:
            created = datetime.fromtimestamp(timestamp_ms / 1000.0, tz=timezone.utc)
        except (OverflowError, OSError, ValueError):
            return None
        if created.year < 2010 or created.year > 2100:
            return None
        return created.isoformat()

    def _extract_posted_ago(self, chunk: str) -> str | None:
        match = self.POSTED_AGO_RE.search(chunk or "")
        if not match:
            return None
        value = re.sub(r"\s+", "", match.group("ago").lower())
        if value == "justnow":
            return "just now"
        if not re.fullmatch(r"\d+[smhdw]", value):
            return None
        # Guard against false positives from huge/noise numbers.
        amount = int(value[:-1])
        unit = value[-1]
        max_by_unit = {"s": 59, "m": 59, "h": 23, "d": 366, "w": 520}
        if amount < 1 or amount > max_by_unit[unit]:
            return None
        return value

    def _format_posted_ago_label(self, posted_ago: str | None) -> str | None:
        if not posted_ago:
            return None
        if posted_ago == "just now":
            return "just now"
        match = re.fullmatch(r"(\d+)([smhdw])", posted_ago)
        if not match:
            return posted_ago
        amount = int(match.group(1))
        unit = match.group(2)
        names = {"s": "second", "m": "minute", "h": "hour", "d": "day", "w": "week"}
        label = names[unit]
        if amount != 1:
            label += "s"
        return f"{amount} {label} ago"

    def _parse_int_count(self, value: str) -> int | None:
        digits = re.sub(r"[^\d]", "", value or "")
        if not digits:
            return None
        try:
            return int(digits)
        except ValueError:
            return None

    def _activity_positions(self, html_text: str) -> list[tuple[str, int]]:
        positions: list[tuple[str, int]] = []
        seen: set[str] = set()
        for match in self.ACTIVITY_URN_RE.finditer(html_text or ""):
            activity_id = match.group(1)
            if activity_id in seen:
                continue
            seen.add(activity_id)
            positions.append((activity_id, match.start()))
        return positions

    def _nearest_activity_id(self, positions: list[tuple[str, int]], offset: int) -> str | None:
        nearest: str | None = None
        for activity_id, start in positions:
            if start <= offset:
                nearest = activity_id
            else:
                break
        return nearest

    def _set_stat_once(self, stats_by_activity: dict[str, dict[str, int | None]], activity_id: str | None, key: str, value: int | None) -> None:
        if not activity_id or value is None:
            return
        bucket = stats_by_activity.setdefault(
            activity_id,
            {
                "impressions": None,
                "reactions": None,
                "comments": None,
                "reposts": None,
                "engagements": None,
            },
        )
        if bucket.get(key) is None:
            bucket[key] = value

    def _extract_engagement_stats_by_activity(self, html_text: str) -> dict[str, dict[str, int | None]]:
        positions = self._activity_positions(html_text or "")
        stats_by_activity: dict[str, dict[str, int | None]] = {}
        if not positions:
            return stats_by_activity

        extractors = [
            (self.IMPRESSIONS_RE, "impressions", lambda match: self._parse_int_count(match.group("count"))),
            (self.REACTIONS_COUNT_RE, "reactions", lambda match: self._parse_int_count(match.group("count"))),
            (self.SOCIAL_PROOF_COUNT_RE, "reactions", lambda match: self._parse_int_count(match.group("count"))),
            (self.REACTIONS_ARIA_RE, "reactions", lambda match: self._parse_int_count(match.group("count"))),
            (
                self.REACTIONS_OTHERS_ARIA_RE,
                "reactions",
                lambda match: (self._parse_int_count(match.group("count")) or 0) + 1,
            ),
            (self.COMMENTS_ARIA_RE, "comments", lambda match: self._parse_int_count(match.group("count"))),
            (self.REPOSTS_ARIA_RE, "reposts", lambda match: self._parse_int_count(match.group("count"))),
        ]
        for pattern, key, value_fn in extractors:
            for match in pattern.finditer(html_text or ""):
                activity_id = self._nearest_activity_id(positions, match.start())
                self._set_stat_once(stats_by_activity, activity_id, key, value_fn(match))

        for activity_id, bucket in stats_by_activity.items():
            reactions = bucket.get("reactions") or 0
            comments = bucket.get("comments") or 0
            reposts = bucket.get("reposts") or 0
            if bucket.get("reactions") is None and bucket.get("comments") is None and bucket.get("reposts") is None:
                continue
            # Normalize missing social counts to zero once any engagement signal exists.
            if bucket.get("reactions") is None:
                bucket["reactions"] = 0
            if bucket.get("comments") is None:
                bucket["comments"] = 0
            if bucket.get("reposts") is None:
                bucket["reposts"] = 0
            bucket["engagements"] = reactions + comments + reposts
            stats_by_activity[activity_id] = bucket
        return stats_by_activity

    def _extract_activity_card_slices(self, html_text: str) -> list[tuple[str, str]]:
        positions = self._activity_positions(html_text or "")
        slices: list[tuple[str, str]] = []
        for index, (activity_id, start) in enumerate(positions):
            end = positions[index + 1][1] if index + 1 < len(positions) else len(html_text or "")
            chunk_start = max(0, start - 12000)
            slices.append((activity_id, (html_text or "")[chunk_start:end]))
        return slices

    def _extract_posts_from_html(self, html_text: str, profile_slug: str, max_posts: int) -> list[dict[str, Any]]:
        posts_by_id: dict[str, dict[str, Any]] = {}
        fetched_at = datetime.now(tz=timezone.utc).isoformat()
        activity_order: list[str] = []
        shared_asset_names = self._shared_local_asset_names(html_text or "")

        for activity_id, chunk in self._extract_activity_card_slices(html_text or ""):
            post_id = f"activity:{activity_id}"
            activity_order.append(post_id)
            commentary_match = self.COMMENTARY_DOM_RE.search(chunk)
            text = self._html_to_plain_text(commentary_match.group("body")) if commentary_match else ""
            posted_ago = self._extract_posted_ago(chunk)
            created_at = self._created_at_from_activity_id(activity_id)
            media_local_paths = self._extract_local_media_from_chunk(chunk, shared_asset_names)
            media_urls = self._extract_remote_media_from_chunk(chunk)
            self._upsert_post(
                posts_by_id,
                post_id,
                fetched_at,
                url=f"https://www.linkedin.com/feed/update/urn:li:activity:{activity_id}",
                text=text or None,
                title=self._title_from_text(text) or None,
                created_at=created_at,
                posted_ago=posted_ago,
                media_local_paths=media_local_paths,
                media_urls=media_urls,
            )

        # Enrich cards (and fixture/public pages) from embedded JSON + commentary text.
        for match in self.EMBEDDED_JSON_RE.finditer(html_text or ""):
            body = match.group("body").strip()
            if not body:
                continue
            try:
                payload = json.loads(body)
            except json.JSONDecodeError:
                continue
            self._collect_posts_from_json(payload, posts_by_id, fetched_at)

        for match in self.COMMENTARY_RE.finditer(html_text or ""):
            text = self._unescape_json_string(match.group("text")).strip()
            if not text:
                continue
            for post_id in activity_order:
                post = posts_by_id.get(post_id)
                if post and not post.get("text"):
                    post["text"] = text
                    if not post.get("title"):
                        post["title"] = self._title_from_text(text)
                    break

        if not posts_by_id:
            for match in self.ACTIVITY_HREF_RE.finditer(html_text or ""):
                url = match.group("url")
                activity_id = self._activity_id_from_url(url)
                post_id = f"activity:{activity_id}" if activity_id else f"url:{url}"
                if post_id not in posts_by_id:
                    activity_order.append(post_id)
                self._upsert_post(posts_by_id, post_id, fetched_at, url=url)

            for match in self.EMBEDDED_JSON_RE.finditer(html_text or ""):
                body = match.group("body").strip()
                if not body:
                    continue
                try:
                    payload = json.loads(body)
                except json.JSONDecodeError:
                    continue
                self._collect_posts_from_json(payload, posts_by_id, fetched_at)

            commentary_texts = self._extract_commentary_dom_texts(html_text or "")
            if commentary_texts:
                ordered_empty = [
                    posts_by_id[post_id]
                    for post_id in activity_order
                    if posts_by_id.get(post_id) and not posts_by_id[post_id].get("text")
                ]
                for index, text in enumerate(commentary_texts):
                    if index < len(ordered_empty):
                        ordered_empty[index]["text"] = text
                        ordered_empty[index]["title"] = self._title_from_text(text)
                    else:
                        synthetic_id = f"commentary:{index}"
                        self._upsert_post(
                            posts_by_id,
                            synthetic_id,
                            fetched_at,
                            url=f"https://www.linkedin.com/in/{profile_slug}/recent-activity/all/",
                            text=text,
                            title=self._title_from_text(text),
                        )

        if not posts_by_id:
            meta_match = self.META_DESCRIPTION_RE.search(html_text or "")
            if meta_match:
                text = html.unescape(meta_match.group("content")).strip()
                if text and "linkedin" not in text.lower():
                    self._upsert_post(
                        posts_by_id,
                        "meta:description",
                        fetched_at,
                        url=f"https://www.linkedin.com/in/{profile_slug}/",
                        text=text,
                        title=self._title_from_text(text),
                    )
                    posts_by_id["meta:description"]["source"] = "public_html_meta"

        for post in posts_by_id.values():
            if not post.get("title"):
                post["title"] = self._title_from_text(str(post.get("text") or "")) or str(post.get("id") or "post")

        stats_by_activity = self._extract_engagement_stats_by_activity(html_text or "")
        for post_id, post in posts_by_id.items():
            activity_id = None
            if str(post_id).startswith("activity:"):
                activity_id = str(post_id).split(":", 1)[1]
            if activity_id and activity_id in stats_by_activity:
                post["stats"] = stats_by_activity[activity_id]

        posts: list[dict[str, Any]] = []
        seen_ids: set[str] = set()
        for post_id in activity_order:
            post = posts_by_id.get(post_id)
            if post is None or post_id in seen_ids:
                continue
            posts.append(post)
            seen_ids.add(post_id)
        for post_id, post in posts_by_id.items():
            if post_id in seen_ids:
                continue
            posts.append(post)
            seen_ids.add(post_id)
        if max_posts > 0:
            posts = posts[:max_posts]
        return posts

    def parse_posts_from_html(self, html_text: str, profile_url: str, max_posts: int = 50) -> dict[str, Any]:
        normalized, slug = self._normalize_profile_url(profile_url)
        posts = self._extract_posts_from_html(html_text, slug, max_posts=max_posts)
        if not posts and self._looks_like_authwall(html_text, normalized):
            raise RuntimeError("public_view_unavailable")
        return {
            "profile_url": normalized,
            "profile_slug": slug,
            "fetched_at": datetime.now(tz=timezone.utc).isoformat(),
            "source": "public_html",
            "post_count": len(posts),
            "posts": posts,
        }

    def _collect_posts_from_json(self, node: Any, posts_by_id: dict[str, dict[str, Any]], fetched_at: str) -> None:
        if isinstance(node, dict):
            urn = str(node.get("urn") or node.get("entityUrn") or node.get("@id") or "")
            urn_match = self.ACTIVITY_URN_RE.search(urn)
            text = ""
            for key in ("text", "articleBody", "description", "headline"):
                value = node.get(key)
                if isinstance(value, str) and value.strip():
                    text = value.strip()
                    break
            commentary = node.get("commentary")
            if not text and isinstance(commentary, dict):
                nested = commentary.get("text")
                if isinstance(nested, str):
                    text = nested.strip()
            if urn_match:
                activity_id = urn_match.group(1)
                post_id = f"activity:{activity_id}"
                self._upsert_post(
                    posts_by_id,
                    post_id,
                    fetched_at,
                    url=f"https://www.linkedin.com/feed/update/urn:li:activity:{activity_id}",
                    text=text or None,
                    created_at=node.get("datePublished") or node.get("createdAt"),
                )
            elif text and not isinstance(commentary, dict):
                post_id = f"json:{abs(hash((text, str(node.get('@type') or ''))))}"
                self._upsert_post(posts_by_id, post_id, fetched_at, text=text, created_at=node.get("datePublished"))
            for key, value in node.items():
                if key == "commentary":
                    continue
                self._collect_posts_from_json(value, posts_by_id, fetched_at)
        elif isinstance(node, list):
            for item in node:
                self._collect_posts_from_json(item, posts_by_id, fetched_at)

    def parse_profile_url(self, profile_url: str) -> dict[str, str]:
        normalized, slug = self._normalize_profile_url(profile_url)
        return {"profile_url": normalized, "profile_slug": slug}

    def fetch_public_posts(self, profile_url: str, max_posts: int = 50) -> dict[str, Any]:
        self.logger.debug(f"fetch_public_posts(profile_url={profile_url}, max_posts={max_posts})")
        normalized, slug = self._normalize_profile_url(profile_url)
        candidate_urls = [
            f"https://www.linkedin.com/in/{slug}/recent-activity/all/",
            f"https://www.linkedin.com/in/{slug}/recent-activity/shares/",
            normalized,
        ]
        last_html = ""
        last_final_url = ""
        last_status = 0
        for candidate in candidate_urls:
            html_text, final_url, status_code = self._fetch_html(candidate)
            last_html, last_final_url, last_status = html_text, final_url, status_code
            if self._looks_like_authwall(html_text, final_url) or status_code == 999:
                self.logger.warning(
                    f"LinkedIn public view blocked status={status_code} final_url={final_url} candidate={candidate}"
                )
                continue
            posts = self._extract_posts_from_html(html_text, slug, max_posts=max_posts)
            if posts:
                return {
                    "profile_url": normalized,
                    "profile_slug": slug,
                    "fetched_at": datetime.now(tz=timezone.utc).isoformat(),
                    "source": "public_html",
                    "post_count": len(posts),
                    "posts": posts,
                    "fetched_from": candidate,
                    "http_status": status_code,
                }
        if self._looks_like_authwall(last_html, last_final_url) or last_status == 999:
            raise RuntimeError("public_view_unavailable")
        return {
            "profile_url": normalized,
            "profile_slug": slug,
            "fetched_at": datetime.now(tz=timezone.utc).isoformat(),
            "source": "public_html",
            "post_count": 0,
            "posts": [],
            "fetched_from": last_final_url or normalized,
            "http_status": last_status,
        }


if __name__ == "__main__":
    linkedin_client = LinkedInClient()
    print(linkedin_client.parse_profile_url("https://www.linkedin.com/in/example-user/"))
    sample_html = '<html><body><a href="https://www.linkedin.com/feed/update/urn:li:activity:123">x</a><script type="application/ld+json">{"@type":"SocialMediaPosting","articleBody":"Hello world","@id":"urn:li:activity:123"}</script></body></html>'
    print(linkedin_client.parse_posts_from_html(sample_html, "https://www.linkedin.com/in/example-user/", max_posts=5))
