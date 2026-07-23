from rapidfuzz import fuzz
import pandas as pd

from app.services.schema_service import SchemaService, get_schema_service


class MappingService:
    """Авто- и ручной маппинг колонок файла → canonical schema.

    Пользователь видит русские display names; расчёты работают с canonical keys.
    """

    def __init__(self, schema: SchemaService | None = None):
        self.schema = schema or get_schema_service()
        self.canonical_columns = self.schema.canonical_alias_map()

    def normalize(self, s: str) -> str:
        return str(s).strip().lower().replace("\n", " ").replace("ё", "е")

    def auto_map(self, columns, template_key: str | None = None) -> dict:
        """Вернуть {canonical: source_column}.

        Если указан template_key — сопоставляем только поля этого шаблона.
        """
        if template_key:
            candidates = self.schema.template_fields(template_key, include_optional=True)
        else:
            candidates = list(self.canonical_columns.keys())

        mapped = {}
        used_sources = set()
        normalized = {col: self.normalize(col) for col in columns}

        for canon in candidates:
            aliases = self.canonical_columns.get(canon, self.schema.aliases(canon))
            alias_norm = [self.normalize(a) for a in aliases]
            best_col = None
            best_score = 0
            for col, norm in normalized.items():
                if col in used_sources:
                    continue
                score = max([fuzz.ratio(norm, alias) for alias in alias_norm] + [0])
                # точное совпадение display name / alias — приоритет
                if norm in alias_norm:
                    score = 100
                if score > best_score:
                    best_score = score
                    best_col = col
            if best_col is not None and best_score >= 80:
                mapped[canon] = best_col
                used_sources.add(best_col)
        return mapped

    def apply_mapping(self, df: pd.DataFrame, mapping: dict) -> pd.DataFrame:
        reverse = {v: k for k, v in mapping.items() if v in df.columns}
        return df.rename(columns=reverse).copy()

    def mapping_for_ui(self, mapping: dict) -> dict:
        """Представление маппинга для UI: русское имя поля → исходная колонка."""
        return {self.schema.display_name(canon): source for canon, source in mapping.items()}

    def unmapped_required(self, mapping: dict, template_key: str) -> list:
        missing = [f for f in self.schema.required_fields(template_key) if f not in mapping]
        return [self.schema.display_name(f) for f in missing]

    def available_targets_ru(self, template_key: str) -> dict:
        """canonical → display_name_ru для ручного маппинга."""
        return {
            f: self.schema.display_name(f)
            for f in self.schema.template_fields(template_key, include_optional=True)
        }
