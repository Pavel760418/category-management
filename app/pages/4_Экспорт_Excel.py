import streamlit as st
import pandas as pd
from app.services.mapping_service import MappingService
from app.services.calculation_service import CalculationService
from app.services.validation_service import validate_sku_df
from app.services.excel_export_service import ExcelExportService

st.set_page_config(page_title="Экспорт Excel", layout="wide")
st.title("📤 Экспорт итогового Excel")

sku_file = st.session_state.get("sku_file")
comp_file = st.session_state.get("comp_file")
goals_file = st.session_state.get("goals_file")

if not sku_file:
    st.warning("Невозможно сформировать итоговый файл без SKU-данных.")
    st.stop()

ms = MappingService()
calc = CalculationService()
base = pd.read_excel(sku_file)
base = ms.apply_mapping(base, ms.auto_map(base.columns))
base = calc.enrich_base(base)
issues = validate_sku_df(base)
quality_df = pd.DataFrame(issues, columns=["severity", "message", "column"]) if issues else pd.DataFrame(columns=["severity", "message", "column"])
comp = pd.read_excel(comp_file) if comp_file else pd.DataFrame(columns=["competitor_name", "category", "price_index"])
goals = pd.read_excel(goals_file) if goals_file else pd.DataFrame(columns=["metric_name", "target_3m", "target_6m"])
kpi = calc.build_kpis(base, goals)
abc = calc.abc_analysis(base)
turnover = base[[c for c in ["sku_code", "sku_name", "subcategory", "inventory_turnover", "stock_days", "stock_qty"] if c in base.columns]].copy()
purchase = calc.purchase_plan(base)
shelf = calc.shelf_efficiency(base)
lfl = base[[c for c in ["sku_code", "sku_name", "sales_value", "prior_sales_value", "lfl_sales_pct", "gross_profit", "prior_gp_value"] if c in base.columns]].copy()
status = pd.DataFrame([
    ["SKU file", bool(sku_file), "Полностью загружен" if sku_file else "Не загружен"],
    ["Competitor file", bool(comp_file), "Загружен" if comp_file else "Не загружен"],
    ["Goals file", bool(goals_file), "Загружен" if goals_file else "Не загружен"],
], columns=["source", "loaded", "comment"])
limitations = []
if comp.empty:
    limitations.append(["Конкурентный анализ ограничен: файл конкурентов не загружен"])
if "shelf_meters" not in base.columns or base.get("shelf_meters", pd.Series(dtype=float)).fillna(0).sum() == 0:
    limitations.append(["Анализ выкладки ограничен: нет данных по длине выкладки"])
if "prior_sales_value" not in base.columns or base.get("prior_sales_value", pd.Series(dtype=float)).fillna(0).sum() == 0:
    limitations.append(["LFL рассчитан частично или недоступен: отсутствуют данные прошлого года"])
limitations_df = pd.DataFrame(limitations or [["Ограничений анализа не выявлено"]], columns=["limitation"])
instruction_text = """Файл является управленческим инструментом категорийного менеджмента.\n\n1. Основной источник данных — лист «Данные SKU».\n2. Все аналитические листы обновляются от базы данных автоматически.\n3. При отсутствии части файлов система формирует анализ по доступным данным и явно показывает ограничения.\n4. Цветовая логика: зелёный — цель выполнена, жёлтый — риск, красный — проблема/превышение.\n5. Для дней запаса и количества SKU логика обратная: превышение цели считается негативным отклонением.\n6. Главный экран нужно читать сверху вниз: роль категории → KPI → статусы данных → ограничения → детализация."""
exporter = ExcelExportService()
out = exporter.export("data/output/category_management_bi_output.xlsx", base, kpi, abc, turnover, purchase, shelf, lfl, comp, status, quality_df, limitations_df, instruction_text)
with open(out, "rb") as f:
    st.download_button("Скачать итоговый Excel", f, file_name="category_management_bi_output.xlsx")
