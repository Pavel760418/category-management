import pandas as pd

REQUIRED_SKU = [
    "sku_code", "sku_name", "category", "subcategory",
    "sales_value", "sales_qty", "cogs_value", "stock_qty", "purchase_price"
]
OPTIONAL_SKU = [
    "shelf_meters", "prior_sales_value", "prior_sales_qty", "prior_gp_value",
    "store_name", "format_name", "period_months", "current_role"
]


def validate_sku_df(df: pd.DataFrame):
    issues = []
    if df.empty:
        issues.append(("error", "Файл пустой или не прочитан", None))
        return issues
    missing = [c for c in REQUIRED_SKU if c not in df.columns]
    for c in missing:
        issues.append(("error", f"Отсутствует обязательная колонка: {c}", c))
    for c in ["sales_value", "sales_qty", "cogs_value", "stock_qty", "purchase_price"]:
        if c in df.columns:
            bad = pd.to_numeric(df[c], errors="coerce").isna().sum()
            if bad > 0:
                issues.append(("warning", f"Колонка {c} содержит {bad} нечисловых значений", c))
    blank_rows = df.isna().all(axis=1).sum()
    if blank_rows:
        issues.append(("warning", f"Пустых строк: {blank_rows}", None))
    if "sku_code" in df.columns:
        dup = df["sku_code"].astype(str).duplicated().sum()
        if dup:
            issues.append(("warning", f"Дубликатов sku_code: {dup}", "sku_code"))
    return issues
