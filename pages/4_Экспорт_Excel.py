import streamlit as st
import pandas as pd

from app.services.mapping_service import MappingService
from app.services.calculation_service import CalculationService
from app.services.validation_service import validate_sku_df
from app.services.excel_export_service import ExcelExportService
from app.services.schema_service import get_schema_service
from app.utils.io import read_template_excel

st.set_page_config(page_title="Экспорт Excel", layout="wide")
st.title("📤 Экспорт итогового Excel")

schema = get_schema_service()
ms = MappingService(schema)
sku_file = st.session_state.get("sku_file")
comp_file = st.session_state.get("comp_file")
goals_file = st.session_state.get("goals_file")

if not sku_file:
    st.warning("Невозможно сформировать итоговый файл без данных SKU.")
    st.stop()

calc = CalculationService()

base = st.session_state.get("mapped_df_sku")
if base is None:
    base = read_template_excel(sku_file, "sku")
    base = ms.apply_mapping(base, ms.auto_map(base.columns, template_key="sku"))
base = calc.enrich_base(base)

issues = validate_sku_df(base, schema)
quality_df = (
    pd.DataFrame(issues, columns=["уровень", "сообщение", "колонка"])
    if issues
    else pd.DataFrame(columns=["уровень", "сообщение", "колонка"])
)

if comp_file:
    comp = st.session_state.get("mapped_df_competitor")
    if comp is None:
        comp = read_template_excel(comp_file, "competitor")
        comp = ms.apply_mapping(comp, ms.auto_map(comp.columns, template_key="competitor"))
else:
    comp = pd.DataFrame(columns=["competitor_name", "category", "price_index"])

if goals_file:
    goals = st.session_state.get("mapped_df_goals")
    if goals is None:
        goals = read_template_excel(goals_file, "goals")
        goals = ms.apply_mapping(goals, ms.auto_map(goals.columns, template_key="goals"))
else:
    goals = pd.DataFrame(columns=["metric_name", "target_3m", "target_6m"])

kpi = calc.build_kpis(base, goals)
abc = calc.abc_analysis(base)
turnover = base[
    [c for c in ["sku_code", "sku_name", "subcategory", "inventory_turnover", "stock_days", "stock_qty"] if c in base.columns]
].copy()
purchase = calc.purchase_plan(base)
shelf = calc.shelf_efficiency(base)
lfl = base[
    [
        c
        for c in [
            "sku_code",
            "sku_name",
            "sales_value",
            "prior_sales_value",
            "lfl_sales_pct",
            "gross_profit",
            "prior_gp_value",
        ]
        if c in base.columns
    ]
].copy()

status = pd.DataFrame(
    [
        ["Данные SKU", bool(sku_file), "Полностью загружен" if sku_file else "Не загружен"],
        ["Конкуренты", bool(comp_file), "Загружен" if comp_file else "Не загружен"],
        ["Цели категории", bool(goals_file), "Загружен" if goals_file else "Не загружен"],
    ],
    columns=["источник", "загружен", "комментарий"],
)

limitations = []
if comp.empty:
    limitations.append(["Конкурентный анализ ограничен: файл конкурентов не загружен"])
if "shelf_meters" not in base.columns or base.get("shelf_meters", pd.Series(dtype=float)).fillna(0).sum() == 0:
    limitations.append(["Анализ выкладки ограничен: нет данных по длине выкладки"])
if "prior_sales_value" not in base.columns or base.get("prior_sales_value", pd.Series(dtype=float)).fillna(0).sum() == 0:
    limitations.append(["LFL рассчитан частично или недоступен: отсутствуют данные прошлого года"])
limitations_df = pd.DataFrame(limitations or [["Ограничений анализа не выявлено"]], columns=["ограничение"])

instruction_text = (
    "Файл является управленческим инструментом категорийного менеджмента.\n\n"
    "1. Основной источник данных — лист «Данные SKU».\n"
    "2. Все аналитические листы обновляются от базы данных автоматически.\n"
    "3. При отсутствии части файлов система формирует анализ по доступным данным и явно показывает ограничения.\n"
    "4. Цветовая логика: зелёный — цель выполнена, жёлтый — риск, красный — проблема/превышение.\n"
    "5. Для дней запаса и количества SKU логика обратная: превышение цели считается негативным отклонением.\n"
    "6. Главный экран нужно читать сверху вниз: роль категории → KPI → статусы данных → ограничения → детализация.\n"
    "7. Пользовательские шаблоны загрузки полностью на русском языке; внутренние технические ключи скрыты."
)

# В экспортном Excel для пользователя показываем русские заголовки колонок
def _ru(df: pd.DataFrame) -> pd.DataFrame:
    if df is None or df.empty:
        return df
    mapping = {c: schema.display_name(c) if c in schema.fields else c for c in df.columns}
    # дополнительные вычисляемые поля
    extra = {
        "gross_profit": "Валовая прибыль, руб.",
        "margin_pct": "Маржа %",
        "inventory_turnover": "Оборачиваемость",
        "stock_days": "Дни запаса",
        "revenue_per_shelf": "Выручка на пог. м",
        "gp_per_shelf": "ВП на пог. м",
        "lfl_sales_pct": "LFL продаж, %",
        "abc_class": "ABC-класс",
        "cum_share": "Накопленная доля",
        "sales_per_meter": "Продажи на пог. м",
        "gp_per_meter": "ВП на пог. м",
        "purchase_qty_needed": "К закупке, шт.",
        "purchase_budget": "Бюджет закупки, руб.",
        "target_stock_qty": "Целевой остаток, шт.",
        "code": "Код KPI",
        "name": "Показатель",
        "actual": "Факт",
        "target": "Цель",
        "ratio": "Индекс",
        "status": "Статус",
        "direction": "Направление",
    }
    for k, v in extra.items():
        if k in mapping and mapping[k] == k:
            mapping[k] = v
    return df.rename(columns=mapping)


exporter = ExcelExportService()
out = exporter.export(
    "data/output/category_management_bi_output.xlsx",
    _ru(base),
    _ru(kpi),
    _ru(abc),
    _ru(turnover),
    _ru(purchase),
    _ru(shelf),
    _ru(lfl),
    _ru(comp),
    status,
    quality_df,
    limitations_df,
    instruction_text,
)
with open(out, "rb") as f:
    st.download_button(
        "Скачать итоговый Excel",
        f,
        file_name="Итог_категорийный_менеджмент_BI.xlsx",
    )
