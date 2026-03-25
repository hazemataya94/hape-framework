from pathlib import Path

import pytest

from core.errors import HapeValidationError
from services.init_cicd.renderer.template_renderer import TemplateRenderer


def test_render_text_replaces_placeholders() -> None:
    template_renderer = TemplateRenderer()
    rendered = template_renderer.render_text("name: {{ app_name }}", {"app_name": "demo"})
    assert rendered == "name: demo"


def test_render_text_raises_when_placeholder_missing() -> None:
    template_renderer = TemplateRenderer()
    with pytest.raises(HapeValidationError) as exc:
        template_renderer.render_text("name: {{ app_name }} value: {{ image_tag }}", {"app_name": "demo"})
    assert exc.value.code == "INIT_CICD_TEMPLATE_PLACEHOLDER_MISSING"


def test_render_file_missing_template(tmp_path: Path) -> None:
    template_renderer = TemplateRenderer()
    with pytest.raises(HapeValidationError) as exc:
        template_renderer.render_file(tmp_path / "missing.tpl", {"app_name": "demo"})
    assert exc.value.code == "INIT_CICD_TEMPLATE_MISSING"


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__]))
