import streamlit as st
import pandas as pd
import plotly.express as px
from app.services.mapping_service import MappingService
from app.services.calculation_service import CalculationService
from app.components.kpi_cards import render_kpi_cards

st.set_page_config(page_title="BI Dashboard", layout="wide")
st.title("🏆 BI-дашборд категории")

sku_file = st.session_state.get("sku_file")
goals_file = st.session_state.get("goals_file")
if not sku_file:
    st.warning("Загрузите SKU-файл на странице «Загрузка данных».")
    st.stop()

base = pd.read_excel(sku_file)
ms = MappingService()
base = ms.apply_mapping(base, ms.auto_map(base.columns))
calc = CalculationService()
base = calc.enrich_base(base)
goals = pd.read_excel(goals_file) if goals_file else pd.DataFrame()
kpi = calc.build_kpis(base, goals)
abc = calc.abc_analysis(base)
shelf = calc.shelf_efficiency(base)

render_kpi_cards(kpi)

col1, col2 = st.columns(2)
with col1:
    st.subheader("ABC по выручке")
    if not abc.empty:
        fig = px.bar(abc.head(20), x="sku_name", y="sales_value", color="abc_class")
        st.plotly_chart(fig, use_container_width=True)
with col2:
    st.subheader("Статус KPI")
    st.dataframe(kpi[["name", "actual", "target", "status"]], use_container_width=True)

st.subheader("Эффективность выкладки")
if shelf.empty:
    st.info("Недостаточно данных по длине выкладки.")
else:
    fig2 = px.bar(shelf, x=shelf.columns[0], y="sales_per_meter", color="gp_per_meter")
    st.plotly_chart(fig2, use_container_width=True)
