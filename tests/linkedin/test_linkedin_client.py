from __future__ import annotations

from pathlib import Path

import pytest

from clients.linkedin_client import LinkedInClient


FIXTURES = Path(__file__).parent / "fixtures"


def test_parse_profile_url_accepts_public_in_slug() -> None:
    linkedin_client = LinkedInClient(request_delay_seconds=0)
    parsed = linkedin_client.parse_profile_url("https://www.linkedin.com/in/example-user")
    assert parsed["profile_slug"] == "example-user"
    assert parsed["profile_url"] == "https://www.linkedin.com/in/example-user/"


def test_parse_profile_url_rejects_non_profile_paths() -> None:
    linkedin_client = LinkedInClient(request_delay_seconds=0)
    with pytest.raises(ValueError):
        linkedin_client.parse_profile_url("https://www.linkedin.com/company/example/")


def test_parse_posts_from_fixture_html() -> None:
    linkedin_client = LinkedInClient(request_delay_seconds=0)
    html_text = (FIXTURES / "public_profile_activity.html").read_text(encoding="utf-8")
    payload = linkedin_client.parse_posts_from_html(
        html_text=html_text,
        profile_url="https://www.linkedin.com/in/example-user/",
        max_posts=10,
    )
    assert payload["post_count"] >= 1
    assert any("Shipping a safer release pipeline." in (post.get("text") or "") for post in payload["posts"])
    assert all(post.get("title") and post.get("title") != "unknown" for post in payload["posts"])


def test_parse_posts_from_authwall_raises() -> None:
    linkedin_client = LinkedInClient(request_delay_seconds=0)
    html_text = (FIXTURES / "blocked_challenge.html").read_text(encoding="utf-8")
    with pytest.raises(RuntimeError, match="public_view_unavailable"):
        linkedin_client.parse_posts_from_html(
            html_text=html_text,
            profile_url="https://www.linkedin.com/in/example-user/",
            max_posts=10,
        )


def test_parse_posts_ignores_recaptcha_script_noise() -> None:
    linkedin_client = LinkedInClient(request_delay_seconds=0)
    html_text = """
    <html><body>
      <script src="recaptcha__en.js"></script>
      <div class='update-components-text relative update-components-update-v2__commentary' dir='ltr'>
        <span class="break-words tvm-parent-container">
          <span dir="ltr">Hello from a saved activity page.</span>
        </span>
      </div>
      <a href="https://www.linkedin.com/feed/update/urn:li:activity:7488860673645371392">x</a>
      <span>1d •</span>
    </body></html>
    """
    payload = linkedin_client.parse_posts_from_html(
        html_text=html_text,
        profile_url="https://www.linkedin.com/in/example-user/",
        max_posts=10,
    )
    assert payload["post_count"] >= 1
    post = payload["posts"][0]
    assert "Hello from a saved activity page." in (post.get("text") or "")
    assert post.get("created_at", "").startswith("2026-07-31")
    assert post.get("posted_ago") == "1d"


def test_extracts_engagement_stats_from_activity_html() -> None:
    linkedin_client = LinkedInClient(request_delay_seconds=0)
    html_text = """
    <html><body>
      <div>urn:li:activity:7488860673645371392</div>
      <div class="update-components-update-v2__commentary"><span class="break-words"><span>Hello stats.</span></span></div>
      <span aria-label="1 reaction"></span>
      <span class="social-details-social-counts__reactions-count">1</span>
      <strong>218 impressions</strong>
      <span aria-label="2 comments on Example User’s post"></span>
      <span aria-label="3 reposts of Example User’s post"></span>
    </body></html>
    """
    payload = linkedin_client.parse_posts_from_html(
        html_text=html_text,
        profile_url="https://www.linkedin.com/in/example-user/",
        max_posts=10,
    )
    assert payload["post_count"] == 1
    stats = payload["posts"][0]["stats"]
    assert stats["impressions"] == 218
    assert stats["reactions"] == 1
    assert stats["comments"] == 2
    assert stats["reposts"] == 3
    assert stats["engagements"] == 6
