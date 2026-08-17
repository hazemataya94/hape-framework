from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from typing import Any


class LinkedInPostFormatter:
    @staticmethod
    def _post_title(post: dict[str, Any]) -> str:
        title = str(post.get("title") or "").strip()
        if title and title.lower() != "unknown":
            return title
        text = str(post.get("text") or "").strip()
        if text:
            first_line = next((line.strip() for line in text.splitlines() if line.strip()), "")
            if first_line:
                return first_line if len(first_line) <= 90 else f"{first_line[:87].rstrip()}..."
        post_id = str(post.get("id") or "").strip()
        return post_id or "Post"

    @staticmethod
    def _parse_created_at(value: str) -> datetime | None:
        raw = (value or "").strip()
        if not raw:
            return None
        try:
            if raw.endswith("Z"):
                raw = raw[:-1] + "+00:00"
            parsed = datetime.fromisoformat(raw)
        except ValueError:
            return None
        if parsed.tzinfo is None:
            return parsed.replace(tzinfo=timezone.utc)
        return parsed.astimezone(timezone.utc)

    @staticmethod
    def _timeline_heading(post: dict[str, Any]) -> str:
        created = LinkedInPostFormatter._parse_created_at(str(post.get("created_at") or ""))
        if created is not None:
            return created.strftime("%Y-%m-%d %H:%M UTC")
        posted_ago = LinkedInPostFormatter._posted_ago_label(str(post.get("posted_ago") or "").strip())
        if posted_ago:
            return posted_ago
        return "Date unknown"

    @staticmethod
    def _posted_ago_label(posted_ago: str) -> str:
        if not posted_ago:
            return ""
        if posted_ago == "just now" or posted_ago.endswith("ago"):
            return posted_ago
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

    @staticmethod
    def _format_count(value: Any) -> str:
        if value is None:
            return "n/a"
        try:
            number = int(value)
        except (TypeError, ValueError):
            return "n/a"
        return f"{number:,}"

    @staticmethod
    def _format_stat_phrase(value: Any, singular: str, plural: str) -> str:
        if value is None:
            return f"n/a {plural}"
        try:
            number = int(value)
        except (TypeError, ValueError):
            return f"n/a {plural}"
        label = singular if number == 1 else plural
        return f"{number:,} {label}"

    @staticmethod
    def _stats_line(stats: dict[str, Any]) -> str:
        return (
            "- Stats: "
            f"{LinkedInPostFormatter._format_stat_phrase(stats.get('impressions'), 'impression', 'impressions')} · "
            f"{LinkedInPostFormatter._format_stat_phrase(stats.get('reactions'), 'reaction', 'reactions')} · "
            f"{LinkedInPostFormatter._format_stat_phrase(stats.get('comments'), 'comment', 'comments')} · "
            f"{LinkedInPostFormatter._format_stat_phrase(stats.get('reposts'), 'repost', 'reposts')} · "
            f"{LinkedInPostFormatter._format_stat_phrase(stats.get('engagements'), 'engagement', 'engagements')}"
        )

    @staticmethod
    def _stats_dict(post: dict[str, Any]) -> dict[str, Any]:
        stats = post.get("stats")
        return stats if isinstance(stats, dict) else {}

    @staticmethod
    def _has_stats(stats: dict[str, Any]) -> bool:
        return any(stats.get(key) is not None for key in ("impressions", "reactions", "comments", "reposts", "engagements"))

    @staticmethod
    def _aggregate_stats(posts: list[dict[str, Any]]) -> dict[str, int]:
        totals = {
            "impressions": 0,
            "reactions": 0,
            "comments": 0,
            "reposts": 0,
            "engagements": 0,
        }
        for post in posts:
            stats = LinkedInPostFormatter._stats_dict(post)
            for key in totals:
                value = stats.get(key)
                if isinstance(value, int):
                    totals[key] += value
        return totals

    @staticmethod
    def to_json(payload: dict[str, Any], indent: int = 2) -> str:
        return json.dumps(payload, indent=indent, ensure_ascii=False, sort_keys=True) + "\n"

    @staticmethod
    def to_markdown(payload: dict[str, Any]) -> str:
        profile_url = str(payload.get("profile_url") or "")
        slug = str(payload.get("profile_slug") or "")
        fetched_at = str(payload.get("fetched_at") or "")
        posts = list(payload.get("posts") or [])
        posts.sort(
            key=lambda post: (
                LinkedInPostFormatter._parse_created_at(str(post.get("created_at") or ""))
                or datetime.min.replace(tzinfo=timezone.utc),
                str(post.get("id") or ""),
            ),
            reverse=True,
        )
        totals = LinkedInPostFormatter._aggregate_stats(posts)
        lines: list[str] = [
            f"# LinkedIn timeline — {slug or profile_url}",
            "",
            f"- Profile: {profile_url}",
            f"- Fetched at: {fetched_at}",
            f"- Post count: {len(posts)}",
            f"- Source: {payload.get('source') or 'public_html'}",
            "",
            "## Totals",
            "",
            f"- Impressions: {LinkedInPostFormatter._format_count(totals['impressions'])}",
            f"- Reactions: {LinkedInPostFormatter._format_count(totals['reactions'])}",
            f"- Comments: {LinkedInPostFormatter._format_count(totals['comments'])}",
            f"- Reposts: {LinkedInPostFormatter._format_count(totals['reposts'])}",
            f"- Engagements: {LinkedInPostFormatter._format_count(totals['engagements'])}",
            "",
            "Newest first.",
            "",
        ]
        if not posts:
            lines.extend(["No posts found in the public view.", ""])
            return "\n".join(lines)

        for post in posts:
            title = LinkedInPostFormatter._post_title(post)
            text = str(post.get("text") or "").strip() or "(no text)"
            url = str(post.get("url") or "")
            posted_ago = LinkedInPostFormatter._posted_ago_label(str(post.get("posted_ago") or "").strip())
            heading = LinkedInPostFormatter._timeline_heading(post)
            stats = LinkedInPostFormatter._stats_dict(post)
            lines.append("---")
            lines.append("")
            lines.append(f"## {heading}")
            lines.append("")
            if posted_ago and heading != posted_ago:
                lines.append(f"- When: {posted_ago}")
            if url:
                lines.append(f"- URL: {url}")
            if LinkedInPostFormatter._has_stats(stats):
                lines.append(LinkedInPostFormatter._stats_line(stats))
            if posted_ago or url or LinkedInPostFormatter._has_stats(stats):
                lines.append("")
            lines.append(text)
            lines.append("")
            media_paths = [str(path) for path in (post.get("media_paths") or []) if str(path).strip()]
            media_urls = [str(url_value) for url_value in (post.get("media_urls") or []) if str(url_value).strip()]
            display_media = media_paths or [url_value for url_value in media_urls if not url_value.startswith("http")]
            remote_media = [url_value for url_value in media_urls if url_value.startswith("http")]
            if display_media:
                for media_index, media_path in enumerate(display_media, start=1):
                    alt = f"{title} photo {media_index}"
                    lines.append(f"![{alt}]({media_path})")
                    lines.append("")
            elif remote_media:
                lines.append("Media:")
                for media_url in remote_media:
                    lines.append(f"- {media_url}")
                lines.append("")
        return "\n".join(lines)


if __name__ == "__main__":
    sample = {
        "profile_url": "https://www.linkedin.com/in/example/",
        "profile_slug": "example",
        "fetched_at": "2026-08-01T00:00:00+00:00",
        "source": "public_html",
        "posts": [
            {
                "id": "activity:1",
                "title": "Hello title",
                "url": "https://www.linkedin.com/feed/update/urn:li:activity:1",
                "created_at": "2026-07-31T07:38:40.900000+00:00",
                "posted_ago": "1d",
                "text": "Hello",
                "media_paths": ["media/1-1.jpg"],
                "media_urls": [],
                "stats": {
                    "impressions": 218,
                    "reactions": 1,
                    "comments": 0,
                    "reposts": 0,
                    "engagements": 1,
                },
            }
        ],
    }
    print(LinkedInPostFormatter.to_markdown(sample))
    print(LinkedInPostFormatter.to_json(sample))
