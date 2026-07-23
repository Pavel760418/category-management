from pathlib import Path
import pandas as pd

from app.services.schema_service import get_schema_service


def read_excel_safe(file, sheet_name=0):
    try:
        return pd.read_excel(file, sheet_name=sheet_name)
    except Exception:
        return pd.DataFrame()


def read_template_excel(file, template_key: str | None = None) -> pd.DataFrame:
    """Прочитать Excel с приоритетом русского имени листа шаблона.

    Если лист с русским названием не найден — берётся первый лист.
    Это сохраняет устойчивость к «грязным» файлам пользователя.
    """
    if file is None:
        return pd.DataFrame()
    try:
        xl = pd.ExcelFile(file)
    except Exception:
        return pd.DataFrame()

    preferred = None
    if template_key:
        try:
            preferred = get_schema_service().template(template_key).get("sheet_name_ru")
        except KeyError:
            preferred = None

    sheet = None
    if preferred and preferred in xl.sheet_names:
        sheet = preferred
    else:
        # пропускаем лист «Инструкция», если есть другие
        non_instruction = [s for s in xl.sheet_names if str(s).strip().lower() not in {"инструкция", "instruction"}]
        sheet = non_instruction[0] if non_instruction else xl.sheet_names[0]

    try:
        return pd.read_excel(xl, sheet_name=sheet)
    except Exception:
        return pd.DataFrame()


def ensure_output_dir(path: str):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    return path
