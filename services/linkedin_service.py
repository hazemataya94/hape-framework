from __future__ import annotations

import shutil
import webbrowser
from pathlib import Path
from typing import Any, Callable

from clients.linkedin_client import LinkedInClient
from core.errors.exceptions import HapeExternalError, HapeOperationError, HapeValidationError
from core.errors.messages.linkedin_error_messages import get_linkedin_error_message
from core.logging import LocalLogging
from utils.file_manager import FileManager
from utils.formatters.linkedin_post_formatter import LinkedInPostFormatter


class LinkedInService:
    DEFAULT_MAX_POSTS = 200
    DEFAULT_FORMAT = "json"
    SUPPORTED_FORMATS = {"json", "markdown", "both"}
    LOGIN_URL = "https://www.linkedin.com/login"
    DEFAULT_OUTPUT_DIR = "linkedin-posts"
    MEDIA_DIR_NAME = "media"

    def __init__(
        self,
        linkedin_client: LinkedInClient | None = None,
        file_manager: FileManager | None = None,
        open_browser: Callable[[str], bool] | None = None,
    ) -> None:
        self.linkedin_client = linkedin_client or LinkedInClient()
        self.file_manager = file_manager or FileManager()
        self.open_browser = open_browser or webbrowser.open
        self.logger = LocalLogging.get_logger("hape.linkedin_service")

    def _validate_max_posts(self, max_posts: int) -> None:
        if not isinstance(max_posts, int) or max_posts <= 0:
            raise HapeValidationError(
                code="LINKEDIN_MAX_POSTS_INVALID",
                message=get_linkedin_error_message("LINKEDIN_MAX_POSTS_INVALID"),
            )

    def _validate_format(self, output_format: str) -> str:
        normalized = (output_format or "").strip().lower()
        if normalized not in self.SUPPORTED_FORMATS:
            raise HapeValidationError(
                code="LINKEDIN_FORMAT_INVALID",
                message=get_linkedin_error_message("LINKEDIN_FORMAT_INVALID"),
            )
        return normalized

    def _validate_profile_url(self, profile_url: str) -> dict[str, str]:
        if not profile_url or not str(profile_url).strip():
            raise HapeValidationError(
                code="LINKEDIN_PROFILE_URL_REQUIRED",
                message=get_linkedin_error_message("LINKEDIN_PROFILE_URL_REQUIRED"),
            )
        try:
            return self.linkedin_client.parse_profile_url(profile_url)
        except ValueError as exc:
            raise HapeValidationError(
                code="LINKEDIN_PROFILE_URL_INVALID",
                message=get_linkedin_error_message("LINKEDIN_PROFILE_URL_INVALID"),
            ) from exc

    def _write_export(self, payload: dict[str, Any], output_dir: str, output_format: str) -> dict[str, Any]:
        if not output_dir or not str(output_dir).strip():
            raise HapeValidationError(
                code="LINKEDIN_OUTPUT_DIR_REQUIRED",
                message=get_linkedin_error_message("LINKEDIN_OUTPUT_DIR_REQUIRED"),
            )
        output_path = Path(output_dir).expanduser()
        try:
            self.file_manager.create_directory(str(output_path))
            written: dict[str, str] = {}
            if output_format in {"json", "both"}:
                json_path = output_path / "posts.json"
                self.file_manager.write_file(str(json_path), LinkedInPostFormatter.to_json(payload))
                written["json"] = str(json_path)
            if output_format in {"markdown", "both"}:
                markdown_path = output_path / "posts.md"
                self.file_manager.write_file(str(markdown_path), LinkedInPostFormatter.to_markdown(payload))
                written["markdown"] = str(markdown_path)
            return {"output_dir": str(output_path), "files": written, **payload}
        except HapeValidationError:
            raise
        except Exception as exc:
            raise HapeOperationError(
                code="LINKEDIN_WRITE_FAILED",
                message=get_linkedin_error_message("LINKEDIN_WRITE_FAILED", output_dir=str(output_path)),
            ) from exc

    def _recent_activity_url(self, profile_slug: str) -> str:
        return f"https://www.linkedin.com/in/{profile_slug}/recent-activity/all/"

    def build_prepare_instructions(
        self,
        profile_url: str,
        output_dir: str = DEFAULT_OUTPUT_DIR,
        html_file_name: str = "recent-activity.html",
    ) -> dict[str, Any]:
        profile = self._validate_profile_url(profile_url)
        recent_activity_url = self._recent_activity_url(profile["profile_slug"])
        output_path = Path(output_dir).expanduser()
        html_path = output_path / html_file_name
        next_command = (
            "hape linkedin posts download \\\n"
            f"  --profile-url {profile['profile_url']} \\\n"
            f"  --output-dir {output_path} \\\n"
            f"  --html-file {html_path} \\\n"
            "  --format both"
        )
        instructions = "\n".join(
            [
                "HAPE LinkedIn posts prepare",
                "",
                "Live unauthenticated fetches often hit LinkedIn's auth wall.",
                "Use a normal browser session, then parse a saved HTML page locally.",
                "HAPE does not collect LinkedIn passwords, cookies, or API tokens.",
                "",
                "Steps:",
                "1. Sign in to LinkedIn in the browser tab that opens (or open the login URL printed below).",
                "2. After login, open your Recent activity page:",
                f"   {recent_activity_url}",
                "3. Scroll until the posts you want are visible on the page.",
                "4. Save the page as HTML:",
                "   - Chrome/Edge: File → Save Page As… → Webpage, Complete (or HTML Only).",
                "   - Safari: File → Save As… → Format: Page Source / Web Archive if HTML is unavailable, prefer Page Source.",
                "   - Firefox: File → Save Page As… → Web Page, HTML only.",
                f"5. Save the file as: {html_path}",
                "6. Run the download command printed below with --html-file pointing at that saved page.",
                "",
                "Do not paste credentials into the terminal.",
                "Prefer LinkedIn Settings → Data privacy → Get a copy of your data for a full personal archive.",
            ]
        )
        return {
            "profile_url": profile["profile_url"],
            "profile_slug": profile["profile_slug"],
            "login_url": self.LOGIN_URL,
            "recent_activity_url": recent_activity_url,
            "suggested_html_file": str(html_path),
            "suggested_output_dir": str(output_path),
            "next_command": next_command,
            "instructions": instructions,
        }

    def open_login_url(self, login_url: str | None = None) -> dict[str, Any]:
        target_url = (login_url or self.LOGIN_URL).strip()
        browser_opened = False
        browser_error: str | None = None
        try:
            browser_opened = bool(self.open_browser(target_url))
            if not browser_opened:
                browser_error = get_linkedin_error_message(
                    "LINKEDIN_BROWSER_OPEN_FAILED",
                    url=target_url,
                )
        except Exception as exc:  # noqa: BLE001 - prepare must stay operator-friendly
            browser_opened = False
            browser_error = get_linkedin_error_message(
                "LINKEDIN_BROWSER_OPEN_FAILED",
                url=target_url,
            )
            self.logger.warning("browser open failed for LinkedIn login: %s", exc)
        return {
            "login_url": target_url,
            "browser_opened": browser_opened,
            "browser_error": browser_error,
        }

    def prepare_browser_export(
        self,
        profile_url: str,
        output_dir: str = DEFAULT_OUTPUT_DIR,
        open_login: bool = True,
    ) -> dict[str, Any]:
        self.logger.debug(
            "prepare_browser_export(profile_url=%s, output_dir=%s, open_login=%s)",
            profile_url,
            output_dir,
            open_login,
        )
        plan = self.build_prepare_instructions(profile_url=profile_url, output_dir=output_dir)
        if not open_login:
            return {
                **plan,
                "browser_opened": False,
                "browser_error": None,
            }
        opened = self.open_login_url(plan["login_url"])
        return {
            **plan,
            "browser_opened": opened["browser_opened"],
            "browser_error": opened["browser_error"],
        }

    def _materialize_local_media(self, payload: dict[str, Any], html_file: Path, output_dir: Path) -> dict[str, Any]:
        posts = payload.get("posts") or []
        if not posts:
            return payload
        media_dir = output_dir / self.MEDIA_DIR_NAME
        media_dir.mkdir(parents=True, exist_ok=True)
        html_parent = html_file.parent
        for post in posts:
            local_refs = list(post.get("media_local_paths") or [])
            materialized: list[str] = []
            for index, rel in enumerate(local_refs, start=1):
                source = (html_parent / rel).resolve()
                if not source.is_file():
                    continue
                try:
                    if source.stat().st_size < LinkedInClient.MIN_LOCAL_MEDIA_BYTES:
                        continue
                except OSError:
                    continue
                extension = self.linkedin_client._detect_image_extension(source)
                if not extension:
                    continue
                activity = str(post.get("id") or "post").replace(":", "-")
                target_name = f"{activity}-{index}.{extension}"
                target = media_dir / target_name
                shutil.copy2(source, target)
                relative = f"{self.MEDIA_DIR_NAME}/{target_name}"
                if relative not in materialized:
                    materialized.append(relative)
            post["media_paths"] = materialized
            # Prefer local extracted photos in markdown/json consumers.
            if materialized:
                post["media_urls"] = list(dict.fromkeys([*(post.get("media_urls") or []), *materialized]))
        payload["posts"] = posts
        payload["post_count"] = len(posts)
        return payload

    def download_public_posts(self, profile_url: str, output_dir: str, max_posts: int = DEFAULT_MAX_POSTS, output_format: str = DEFAULT_FORMAT, html_file: str | None = None) -> dict[str, Any]:
        self.logger.debug(
            f"download_public_posts(profile_url={profile_url}, output_dir={output_dir}, max_posts={max_posts}, output_format={output_format}, html_file={html_file})"
        )
        profile = self._validate_profile_url(profile_url)
        self._validate_max_posts(max_posts)
        normalized_format = self._validate_format(output_format)
        html_path: Path | None = None

        try:
            if html_file:
                if not str(html_file).strip():
                    raise HapeValidationError(
                        code="LINKEDIN_HTML_FILE_REQUIRED",
                        message=get_linkedin_error_message("LINKEDIN_HTML_FILE_REQUIRED"),
                    )
                html_path = Path(html_file).expanduser()
                if not html_path.is_file():
                    raise HapeValidationError(
                        code="LINKEDIN_HTML_FILE_NOT_FOUND",
                        message=get_linkedin_error_message("LINKEDIN_HTML_FILE_NOT_FOUND", html_file=str(html_path)),
                    )
                html_text = self.file_manager.read_file(str(html_path))
                payload = self.linkedin_client.parse_posts_from_html(
                    html_text=html_text,
                    profile_url=profile["profile_url"],
                    max_posts=max_posts,
                )
                payload["source"] = "public_html_file"
            else:
                payload = self.linkedin_client.fetch_public_posts(
                    profile_url=profile["profile_url"],
                    max_posts=max_posts,
                )
        except HapeValidationError:
            raise
        except RuntimeError as exc:
            if str(exc) == "public_view_unavailable":
                raise HapeExternalError(
                    code="LINKEDIN_PUBLIC_VIEW_UNAVAILABLE",
                    message=get_linkedin_error_message(
                        "LINKEDIN_PUBLIC_VIEW_UNAVAILABLE",
                        profile_url=profile["profile_url"],
                    ),
                ) from exc
            raise HapeExternalError(
                code="LINKEDIN_PARSE_FAILED",
                message=get_linkedin_error_message("LINKEDIN_PARSE_FAILED", profile_url=profile["profile_url"]),
            ) from exc
        except Exception as exc:
            raise HapeExternalError(
                code="LINKEDIN_FETCH_FAILED",
                message=get_linkedin_error_message("LINKEDIN_FETCH_FAILED", profile_url=profile["profile_url"]),
            ) from exc

        output_path = Path(output_dir).expanduser()
        if html_path is not None:
            try:
                payload = self._materialize_local_media(payload=payload, html_file=html_path, output_dir=output_path)
            except Exception as exc:
                raise HapeOperationError(
                    code="LINKEDIN_WRITE_FAILED",
                    message=get_linkedin_error_message("LINKEDIN_WRITE_FAILED", output_dir=str(output_path)),
                ) from exc

        return self._write_export(payload=payload, output_dir=output_dir, output_format=normalized_format)


if __name__ == "__main__":
    print(LinkedInService.DEFAULT_FORMAT)
