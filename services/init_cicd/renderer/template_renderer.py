import re
from pathlib import Path

from core.errors import HapeExternalError, HapeValidationError
from core.logging import LocalLogging


class TemplateRenderer:
    PLACEHOLDER_PATTERN = re.compile(r"\{\{\s*([a-zA-Z0-9_]+)\s*\}\}")

    def __init__(self) -> None:
        self.logger = LocalLogging.get_logger("hape.template_renderer")

    def _replace_placeholder(self, template_text: str, key: str, value: str) -> str:
        pattern = re.compile(r"\{\{\s*" + re.escape(key) + r"\s*\}\}")
        return pattern.sub(value, template_text)

    def render_text(self, template_text: str, context: dict[str, str]) -> str:
        self.logger.debug("render_text(template_text: <str>, context: <dict>)")
        rendered = template_text
        for key, value in context.items():
            rendered = self._replace_placeholder(template_text=rendered, key=key, value=str(value))
        missing = self.PLACEHOLDER_PATTERN.findall(rendered)
        if missing:
            raise HapeValidationError(
                code="INIT_CICD_TEMPLATE_PLACEHOLDER_MISSING",
                message=f"Template placeholder values are missing: {sorted(set(missing))}.",
                context={"renderer": "TemplateRenderer"},
            )
        return rendered

    def render_file(self, template_path: Path, context: dict[str, str]) -> str:
        self.logger.debug("render_file(template_path: <path>, context: <dict>)")
        if not template_path.exists():
            raise HapeValidationError(
                code="INIT_CICD_TEMPLATE_MISSING",
                message=f"Template file not found: {template_path}",
                context={"template_path": str(template_path)},
            )
        try:
            template_text = template_path.read_text(encoding="utf-8")
            return self.render_text(template_text=template_text, context=context)
        except HapeValidationError:
            raise
        except Exception as exc:
            raise HapeExternalError(
                code="INIT_CICD_TEMPLATE_RENDER_FAILED",
                message=f"Failed to render template: {template_path}",
                context={"template_path": str(template_path)},
            ) from exc


if __name__ == "__main__":
    template_renderer = TemplateRenderer()
    print(template_renderer.render_text("name: {{ app_name }}", {"app_name": "demo"}))
