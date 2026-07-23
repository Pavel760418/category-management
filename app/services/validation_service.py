import pandas as pd

from app.services.schema_service import SchemaService, get_schema_service


NUMERIC_SKU = [
    "sales_value",
    "sales_qty",
    "cogs_value",
    "stock_qty",
    "purchase_price",
]


def validate_sku_df(df: pd.DataFrame, schema: SchemaService | None = None):
    schema = schema or get_schema_service()
    required = schema.required_fields("sku")
    issues = []
    if df.empty:
        issues.append(("error", "Файл пустой или не прочитан", None))
        return issues

    missing = [c for c in required if c not in df.columns]
    for c in missing:
        label = schema.display_name(c)
        issues.append(("error", f"Отсутствует обязательная колонка: {label}", label))

    for c in NUMERIC_SKU:
        if c in df.columns:
            bad = pd.to_numeric(df[c], errors="coerce").isna().sum()
            if bad > 0:
                label = schema.display_name(c)
                issues.append(
                    ("warning", f"Колонка «{label}» содержит {bad} нечисловых значений", label)
                )

    blank_rows = df.isna().all(axis=1).sum()
    if blank_rows:
        issues.append(("warning", f"Пустых строк: {blank_rows}", None))

    if "sku_code" in df.columns:
        dup = df["sku_code"].astype(str).duplicated().sum()
        if dup:
            label = schema.display_name("sku_code")
            issues.append(("warning", f"Дубликатов в колонке «{label}»: {dup}", label))
    return issues


def validate_by_template(df: pd.DataFrame, template_key: str, schema: SchemaService | None = None):
    """Универсальная проверка обязательных полей шаблона с русскими сообщениями."""
    schema = schema or get_schema_service()
    issues = []
    if df.empty:
        issues.append(("error", "Файл пустой или не прочитан", None))
        return issues
    for c in schema.required_fields(template_key):
        if c not in df.columns:
            label = schema.display_name(c)
            issues.append(("error", f"Отсутствует обязательная колонка: {label}", label))
    return issues


# Обратная совместимость: константы с canonical names для внутренних тестов/импортов
REQUIRED_SKU = [
    "sku_code",
    "sku_name",
    "category",
    "subcategory",
    "sales_value",
    "sales_qty",
    "cogs_value",
    "stock_qty",
    "purchase_price",
]
OPTIONAL_SKU = [
    "shelf_meters",
    "prior_sales_value",
    "prior_sales_qty",
    "prior_gp_value",
    "store_name",
    "format_name",
    "period_months",
    "current_role",
]
