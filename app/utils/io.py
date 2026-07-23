from pathlib import Path
import pandas as pd


def read_excel_safe(file, sheet_name=0):
    try:
        return pd.read_excel(file, sheet_name=sheet_name)
    except Exception:
        return pd.DataFrame()


def ensure_output_dir(path: str):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    return path
