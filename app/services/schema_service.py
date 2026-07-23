"""Слой метаданных полей и шаблонов.

Разделение ответственности:
- canonical keys — для расчётов, валидации и бизнес-логики;
- display_name_ru / description_ru — только для UI и Excel-шаблонов;
- aliases_ru / aliases_en — для автосопоставления колонок.
"""

from __future__ import annotations

from functools import lru_cache
from typing import Any, Dict, List, Optional

from app.services.config_service import load_yaml


class SchemaService:
    def __init__(self):
        self._fields_cfg = load_yaml("field_schema.yaml")
        self._templates_cfg = load_yaml("templates_meta.yaml")
        self.fields: Dict[str, dict] = self._fields_cfg.get("fields", {})
        self.metric_aliases: Dict[str, dict] = self._fields_cfg.get("metric_aliases", {})
        self.templates: Dict[str, dict] = self._templates_cfg.get("templates", {})

    def display_name(self, canonical: str) -> str:
        meta = self.fields.get(canonical, {})
        return meta.get("display_name_ru") or canonical

    def description(self, canonical: str) -> str:
        return self.fields.get(canonical, {}).get("description_ru", "")

    def example(self, canonical: str) -> Any:
        return self.fields.get(canonical, {}).get("example_ru")

    def aliases(self, canonical: str) -> List[str]:
        meta = self.fields.get(canonical, {})
        result = [canonical, self.display_name(canonical)]
        result.extend(meta.get("aliases_ru") or [])
        result.extend(meta.get("aliases_en") or [])
        # unique, preserve order
        seen = set()
        ordered = []
        for a in result:
            key = str(a).strip().lower()
            if key and key not in seen:
                seen.add(key)
                ordered.append(str(a))
        return ordered

    def canonical_alias_map(self) -> Dict[str, List[str]]:
        return {name: self.aliases(name) for name in self.fields}

    def template(self, key: str) -> dict:
        if key not in self.templates:
            raise KeyError(f"Unknown template key: {key}")
        return self.templates[key]

    def template_keys(self) -> List[str]:
        return list(self.templates.keys())

    def template_fields(self, key: str, include_optional: bool = True) -> List[str]:
        tpl = self.template(key)
        fields = list(tpl.get("required_fields") or [])
        if include_optional:
            fields.extend(tpl.get("optional_fields") or [])
        return fields

    def required_fields(self, key: str) -> List[str]:
        return list(self.template(key).get("required_fields") or [])

    def optional_fields(self, key: str) -> List[str]:
        return list(self.template(key).get("optional_fields") or [])

    def field_headers_ru(self, key: str, include_optional: bool = True) -> List[str]:
        return [self.display_name(f) for f in self.template_fields(key, include_optional)]

    def display_map(self, canonicals: Optional[List[str]] = None) -> Dict[str, str]:
        keys = canonicals if canonicals is not None else list(self.fields.keys())
        return {k: self.display_name(k) for k in keys}

    def resolve_metric_code(self, raw: str) -> Optional[str]:
        """Сопоставить русское/английское название KPI с внутренним кодом."""
        if raw is None:
            return None
        norm = str(raw).strip().lower()
        if not norm:
            return None
        for code, meta in self.metric_aliases.items():
            candidates = [code, meta.get("display_name_ru", "")]
            candidates.extend(meta.get("aliases_ru") or [])
            candidates.extend(meta.get("aliases_en") or [])
            if any(norm == str(c).strip().lower() for c in candidates if c):
                return code
        return None

    def metric_display_name(self, code: str) -> str:
        meta = self.metric_aliases.get(code, {})
        return meta.get("display_name_ru") or code

    def field_guide_rows(self, template_key: str) -> List[dict]:
        """Строки для листа «Инструкция» и UI-подсказок."""
        rows = []
        for canonical in self.required_fields(template_key):
            rows.append(
                {
                    "field": self.display_name(canonical),
                    "canonical": canonical,
                    "required": "Обязательное",
                    "description": self.description(canonical),
                    "example": self.example(canonical),
                }
            )
        for canonical in self.optional_fields(template_key):
            rows.append(
                {
                    "field": self.display_name(canonical),
                    "canonical": canonical,
                    "required": "Необязательное",
                    "description": self.description(canonical),
                    "example": self.example(canonical),
                }
            )
        return rows


@lru_cache(maxsize=1)
def get_schema_service() -> SchemaService:
    return SchemaService()
