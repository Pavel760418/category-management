from rapidfuzz import fuzz
import pandas as pd
from app.services.config_service import load_yaml


class MappingService:
    def __init__(self):
        cfg = load_yaml("column_mapping.yaml")
        self.canonical_columns = cfg["canonical_columns"]

    def normalize(self, s: str) -> str:
        return str(s).strip().lower().replace("\n", " ")

    def auto_map(self, columns):
        mapped = {}
        normalized = {col: self.normalize(col) for col in columns}
        for canon, aliases in self.canonical_columns.items():
            best_col = None
            best_score = 0
            alias_norm = [self.normalize(a) for a in aliases]
            for col, norm in normalized.items():
                score = max([fuzz.ratio(norm, alias) for alias in alias_norm] + [0])
                if score > best_score:
                    best_score = score
                    best_col = col
            if best_score >= 80:
                mapped[canon] = best_col
        return mapped

    def apply_mapping(self, df: pd.DataFrame, mapping: dict) -> pd.DataFrame:
        reverse = {v: k for k, v in mapping.items() if v in df.columns}
        out = df.rename(columns=reverse).copy()
        return out
