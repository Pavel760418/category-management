import streamlit as st
import pandas as pd
import plotly.express as px

from app.services.mapping_service import MappingService
from app.services.calculation_service import CalculationService
from app.services.schema_service import get_schema_service
from app.components.kpi_cards import render_kpi_cards
from app.utils.io import read_template_excel

st.set_page_config(page_title="BI Dashboard", layout="wide")
st.title("🏆 BI-дашборд категории")

schema = get_schema_service()
sku_file = st.session_state.get("sku_file")
goals_file = st.session_state.get("goals_file")
if not sku_file:
    st.warning("Загрузите файл данных SKU на странице «Загрузка данных».")
    st.stop()

ms = MappingService(schema)
base = st.session_state.get("mapped_df_sku")
if base is None:
    base = read_template_excel(sku_file, "sku")
    base = ms.apply_mapping(base, ms.auto_map(base.columns, template_key="sku"))

calc = CalculationService()
base = calc.enrich_base(base)

if goals_file:
    goals = st.session_state.get("mapped_df_goals")
    if goals is None:
        goals = read_template_excel(goals_file, "goals")
        goals = ms.apply_mapping(goals, ms.auto_map(goals.columns, template_key="goals"))
else:
    goals = pd.DataFrame()

kpi = calc.build_kpis(base, goals)
abc = calc.abc_analysis(base)
shelf = calc.shelf_efficiency(base)

render_kpi_cards(kpi)

col1, col2 = st.columns(2)
with col1:
    st.subheader("ABC по выручке")
    if not abc.empty:
        abc_view = abc.head(20).rename(columns=schema.display_map(list(abc.columns)))
        x_col = schema.display_name("sku_name")
        y_col = schema.display_name("sales_value")
        color_col = "abc_class" if "abc_class" in abc_view.columns else None
        fig = px.bar(abc_view, x=x_col, y=y_col, color=color_col)
        st.plotly_chart(fig, use_container_width=True)
with col2:
    st.subheader("Статус KPI")
    st.dataframe(
        kpi.rename(columns={"name": "Показатель", "actual": "Факт", "target": "Цель", "status": "Статус"})[
            ["Показатель", "Факт", "Цель", "Статус"]
        ],
        use_container_width=True,
    )

st.subheader("Эффективность выкладки")
if shelf.empty:
    st.info("Недостаточно данных по длине выкладки.")
else:
    shelf_view = shelf.rename(columns=schema.display_map(list(shelf.columns)))
    x_col = shelf_view.columns[0]
    fig2 = px.bar(shelf_view, x=x_col, y="sales_per_meter", color="gp_per_meter")
    st.plotly_chart(fig2, use_container_width=True)
