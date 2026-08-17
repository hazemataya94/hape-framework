from __future__ import annotations

from pathlib import Path

import pytest

from core.errors.exceptions import HapeExternalError, HapeValidationError
from services.linkedin_service import LinkedInService


FIXTURES = Path(__file__).parent / "fixtures"


class _FakeLinkedInClient:
    def __init__(self, payload: dict | None = None, error: Exception | None = None) -> None:
        self.payload = payload
        self.error = error

    def parse_profile_url(self, profile_url: str) -> dict[str, str]:
        if "linkedin.com/in/" not in profile_url:
            raise ValueError("profile_url_invalid")
        slug = profile_url.rstrip("/").split("/")[-1]
        return {"profile_url": f"https://www.linkedin.com/in/{slug}/", "profile_slug": slug}

    def parse_posts_from_html(self, html_text: str, profile_url: str, max_posts: int = 50) -> dict:
        if self.error is not None:
            raise self.error
        assert "activity:111222333444" in html_text or "SocialMediaPosting" in html_text
        return self.payload or {
            "profile_url": profile_url,
            "profile_slug": "example-user",
            "fetched_at": "2026-08-01T00:00:00+00:00",
            "source": "public_html",
            "post_count": 1,
            "posts": [
                {
                    "id": "activity:111222333444",
                    "url": "https://www.linkedin.com/feed/update/urn:li:activity:111222333444",
                    "created_at": "2026-07-01T10:00:00Z",
                    "text": "Shipping a safer release pipeline.",
                    "media_urls": [],
                    "source": "public_html",
                    "fetched_at": "2026-08-01T00:00:00+00:00",
                }
            ],
        }

    def fetch_public_posts(self, profile_url: str, max_posts: int = 50) -> dict:
        if self.error is not None:
            raise self.error
        return self.payload or {
            "profile_url": profile_url,
            "profile_slug": "example-user",
            "fetched_at": "2026-08-01T00:00:00+00:00",
            "source": "public_html",
            "post_count": 1,
            "posts": [
                {
                    "id": "activity:1",
                    "url": "https://www.linkedin.com/feed/update/urn:li:activity:1",
                    "created_at": None,
                    "text": "Hello",
                    "media_urls": [],
                    "source": "public_html",
                    "fetched_at": "2026-08-01T00:00:00+00:00",
                }
            ],
        }


def test_download_public_posts_writes_json_and_markdown(tmp_path: Path) -> None:
    service = LinkedInService(linkedin_client=_FakeLinkedInClient())  # type: ignore[arg-type]
    result = service.download_public_posts(
        profile_url="https://www.linkedin.com/in/example-user/",
        output_dir=str(tmp_path / "out"),
        max_posts=10,
        output_format="both",
    )
    assert result["post_count"] == 1
    assert Path(result["files"]["json"]).is_file()
    assert Path(result["files"]["markdown"]).is_file()
    assert "Shipping a safer release pipeline." not in Path(result["files"]["json"]).read_text(encoding="utf-8")
    assert "Hello" in Path(result["files"]["json"]).read_text(encoding="utf-8")
    assert "Hello" in Path(result["files"]["markdown"]).read_text(encoding="utf-8")


def test_download_public_posts_from_html_file(tmp_path: Path) -> None:
    payload = {
        "profile_url": "https://www.linkedin.com/in/example-user/",
        "profile_slug": "example-user",
        "fetched_at": "2026-08-01T00:00:00+00:00",
        "source": "public_html",
        "post_count": 1,
        "posts": [
            {
                "id": "activity:111222333444",
                "url": "https://www.linkedin.com/feed/update/urn:li:activity:111222333444",
                "created_at": "2026-07-01T10:00:00Z",
                "text": "Shipping a safer release pipeline.",
                "media_urls": [],
                "source": "public_html",
                "fetched_at": "2026-08-01T00:00:00+00:00",
            }
        ],
    }
    service = LinkedInService(linkedin_client=_FakeLinkedInClient(payload=payload))  # type: ignore[arg-type]
    result = service.download_public_posts(
        profile_url="https://www.linkedin.com/in/example-user/",
        output_dir=str(tmp_path / "from-html"),
        max_posts=10,
        output_format="json",
        html_file=str(FIXTURES / "public_profile_activity.html"),
    )
    assert result["source"] == "public_html_file"
    assert "Shipping a safer release pipeline." in Path(result["files"]["json"]).read_text(encoding="utf-8")


def test_download_public_posts_authwall_maps_to_external_error(tmp_path: Path) -> None:
    service = LinkedInService(
        linkedin_client=_FakeLinkedInClient(error=RuntimeError("public_view_unavailable"))  # type: ignore[arg-type]
    )
    with pytest.raises(HapeExternalError) as exc_info:
        service.download_public_posts(
            profile_url="https://www.linkedin.com/in/example-user/",
            output_dir=str(tmp_path / "blocked"),
            max_posts=5,
            output_format="json",
        )
    assert exc_info.value.code == "LINKEDIN_PUBLIC_VIEW_UNAVAILABLE"


def test_download_public_posts_rejects_invalid_format(tmp_path: Path) -> None:
    service = LinkedInService(linkedin_client=_FakeLinkedInClient())  # type: ignore[arg-type]
    with pytest.raises(HapeValidationError) as exc_info:
        service.download_public_posts(
            profile_url="https://www.linkedin.com/in/example-user/",
            output_dir=str(tmp_path / "bad-format"),
            max_posts=5,
            output_format="xml",
        )
    assert exc_info.value.code == "LINKEDIN_FORMAT_INVALID"


def test_prepare_browser_export_prints_plan_and_can_skip_browser(tmp_path: Path) -> None:
    opened: list[str] = []
    service = LinkedInService(
        linkedin_client=_FakeLinkedInClient(),  # type: ignore[arg-type]
        open_browser=lambda url: opened.append(url) or True,
    )
    result = service.prepare_browser_export(
        profile_url="https://www.linkedin.com/in/example-user/",
        output_dir=str(tmp_path / "linkedin-posts"),
        open_login=False,
    )
    assert opened == []
    assert result["browser_opened"] is False
    assert result["login_url"] == "https://www.linkedin.com/login"
    assert result["recent_activity_url"].endswith("/in/example-user/recent-activity/all/")
    assert "Save the page as HTML" in result["instructions"]
    assert "--html-file" in result["next_command"]
    assert str(tmp_path / "linkedin-posts" / "recent-activity.html") in result["suggested_html_file"]


def test_prepare_browser_export_opens_login_url(tmp_path: Path) -> None:
    opened: list[str] = []
    service = LinkedInService(
        linkedin_client=_FakeLinkedInClient(),  # type: ignore[arg-type]
        open_browser=lambda url: opened.append(url) or True,
    )
    result = service.prepare_browser_export(
        profile_url="https://www.linkedin.com/in/example-user/",
        output_dir=str(tmp_path / "linkedin-posts"),
        open_login=True,
    )
    assert opened == ["https://www.linkedin.com/login"]
    assert result["browser_opened"] is True
    assert result["browser_error"] is None


def test_public_view_unavailable_message_mentions_prepare() -> None:
    from core.errors.messages.linkedin_error_messages import get_linkedin_error_message

    message = get_linkedin_error_message(
        "LINKEDIN_PUBLIC_VIEW_UNAVAILABLE",
        profile_url="https://www.linkedin.com/in/example-user/",
    )
    assert "hape linkedin posts prepare" in message
    assert "--html-file" in message
