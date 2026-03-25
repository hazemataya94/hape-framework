from typing import Any

from core.errors.exceptions import HapeValidationError


class TriggerParser:
    _NAME_FIELDS_BY_TYPE = {
        "pod": "pod",
        "deployment": "deployment",
        "node": "node",
        "alert": "alertname",
        "cost": "deployment",
    }

    def _normalize_map(self, value: Any) -> dict[str, str]:
        if value is None:
            return {}
        if not isinstance(value, dict):
            raise HapeValidationError(code="KUBE_AGENT_TRIGGER_MAP_INVALID", message="Trigger labels/annotations must be dictionaries.")
        normalized: dict[str, str] = {}
        for key, item in value.items():
            key_text = str(key).strip()
            item_text = str(item).strip()
            if key_text:
                normalized[key_text] = item_text
        return normalized

    def _normalize_text(self, value: Any) -> str:
        if value is None:
            return ""
        return str(value).strip()

    def parse(self, raw_trigger: dict[str, Any]) -> dict[str, Any]:
        if not isinstance(raw_trigger, dict):
            raise HapeValidationError(code="KUBE_AGENT_TRIGGER_RAW_INVALID", message="raw_trigger must be a dictionary.")
        trigger_type = self._normalize_text(raw_trigger.get("type") or raw_trigger.get("kind")).lower()
        name = self._normalize_text(raw_trigger.get("name"))
        if trigger_type in self._NAME_FIELDS_BY_TYPE and not name:
            name = self._normalize_text(raw_trigger.get(self._NAME_FIELDS_BY_TYPE[trigger_type]))
        return {
            "type": trigger_type,
            "cluster": self._normalize_text(raw_trigger.get("cluster")),
            "namespace": self._normalize_text(raw_trigger.get("namespace")) or None,
            "name": name,
            "source": self._normalize_text(raw_trigger.get("source")) or "cli",
            "labels": self._normalize_map(raw_trigger.get("labels")),
            "annotations": self._normalize_map(raw_trigger.get("annotations")),
            "metadata": raw_trigger.get("metadata") if isinstance(raw_trigger.get("metadata"), dict) else {},
        }


if __name__ == "__main__":
    trigger_parser = TriggerParser()
    parsed = trigger_parser.parse({"type": "pod", "cluster": "demo", "namespace": "default", "pod": "api"})
    print(parsed["type"], parsed["name"])
