import argparse
import json
from typing import Any

from core.logging import LocalLogging
from services.linkedin_service import LinkedInService


class LinkedInCommands:
    @staticmethod
    def register(subparsers: argparse._SubParsersAction) -> None:
        parser = subparsers.add_parser(
            "linkedin",
            help="linkedin public profile post export (best-effort; browser HTML fallback).",
        )
        parser.set_defaults(func=LinkedInCommands.run_help, parser=parser)
        linkedin_subparsers = parser.add_subparsers(
            dest="linkedin_command",
            metavar="command",
        )
        linkedin_subparsers.required = False

        posts_parser = linkedin_subparsers.add_parser(
            "posts",
            help="public LinkedIn posts operations.",
        )
        posts_parser.set_defaults(func=LinkedInCommands.run_posts_help, parser=posts_parser)
        posts_subparsers = posts_parser.add_subparsers(
            dest="linkedin_posts_command",
            metavar="command",
        )
        posts_subparsers.required = False

        prepare_parser = posts_subparsers.add_parser(
            "prepare",
            help="print save-as-HTML instructions and open LinkedIn login in a browser.",
        )
        prepare_parser.add_argument(
            "--profile-url",
            required=True,
            default=None,
            help="public LinkedIn profile URL (https://www.linkedin.com/in/<slug>/).",
        )
        prepare_parser.add_argument(
            "--output-dir",
            required=False,
            default=LinkedInService.DEFAULT_OUTPUT_DIR,
            help="suggested local output directory for the saved HTML and export files.",
        )
        prepare_parser.add_argument(
            "--no-open",
            action="store_true",
            help="print instructions only; do not open a browser.",
        )
        prepare_parser.set_defaults(func=LinkedInCommands.run_posts_prepare)

        download_parser = posts_subparsers.add_parser(
            "download",
            help="download public posts for a LinkedIn /in/<slug> profile URL.",
        )
        download_parser.add_argument(
            "--profile-url",
            required=True,
            default=None,
            help="public LinkedIn profile URL (https://www.linkedin.com/in/<slug>/).",
        )
        download_parser.add_argument(
            "--output-dir",
            required=True,
            default=None,
            help="directory for posts.json and/or posts.md.",
        )
        download_parser.add_argument(
            "--max-posts",
            required=False,
            default=200,
            type=int,
            help="maximum posts to keep (default: 200).",
        )
        download_parser.add_argument(
            "--format",
            required=False,
            default="json",
            help="output format: json, markdown, or both (default: json).",
        )
        download_parser.add_argument(
            "--html-file",
            required=False,
            default=None,
            help="optional saved public HTML file to parse instead of a live fetch.",
        )
        download_parser.set_defaults(func=LinkedInCommands.run_posts_download)

    @staticmethod
    def run_help(args: Any) -> None:
        args.parser.print_help()

    @staticmethod
    def run_posts_help(args: Any) -> None:
        args.parser.print_help()

    @staticmethod
    def run_posts_prepare(args: Any) -> None:
        LocalLogging.bootstrap()
        linkedin_service = LinkedInService()
        # Print instructions before opening the browser so the operator can read them first.
        result = linkedin_service.prepare_browser_export(
            profile_url=args.profile_url,
            output_dir=args.output_dir,
            open_login=False,
        )
        print(result["instructions"])
        print("")
        print(f"Login URL: {result['login_url']}")
        print(f"Recent activity URL: {result['recent_activity_url']}")
        print(f"Suggested HTML file: {result['suggested_html_file']}")
        print("")
        print("Next command after saving the HTML page:")
        print(result["next_command"])
        if args.no_open:
            print("")
            print("Browser open skipped (--no-open). Open the login URL manually.")
            return
        opened = linkedin_service.open_login_url(result["login_url"])
        print("")
        if opened.get("browser_error"):
            print(opened["browser_error"])
        elif opened.get("browser_opened"):
            print("Opened LinkedIn login in your default browser.")

    @staticmethod
    def run_posts_download(args: Any) -> None:
        LocalLogging.bootstrap()
        linkedin_service = LinkedInService()
        result = linkedin_service.download_public_posts(
            profile_url=args.profile_url,
            output_dir=args.output_dir,
            max_posts=args.max_posts,
            output_format=args.format,
            html_file=args.html_file,
        )
        print(
            json.dumps(
                {
                    "profile_url": result.get("profile_url"),
                    "profile_slug": result.get("profile_slug"),
                    "post_count": result.get("post_count"),
                    "output_dir": result.get("output_dir"),
                    "files": result.get("files"),
                    "source": result.get("source"),
                },
                indent=2,
                sort_keys=True,
            )
        )


if __name__ == "__main__":
    print(LinkedInCommands)
