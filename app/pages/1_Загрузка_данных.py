import streamlit as st
from app.components.upload_help import render_upload_help

st.set_page_config(page_title="Загрузка данных", layout="wide")
st.title("📥 Загрузка данных")
render_upload_help()

st.subheader("Поддерживаемые шаблоны")
st.markdown("- SKU Upload Template\n- Competitor Upload Template\n- Goals Upload Template")

sku_file = st.file_uploader("Загрузить SKU-файл", type=["xlsx"], key="sku")
comp_file = st.file_uploader("Загрузить файл конкурентов", type=["xlsx"], key="comp")
goals_file = st.file_uploader("Загрузить цели KPI", type=["xlsx"], key="goals")

st.session_state["sku_file"] = sku_file
st.session_state["comp_file"] = comp_file
st.session_state["goals_file"] = goals_file

st.caption("Если часть файлов не загружена, приложение продолжит работу и явно покажет ограничения анализа.")
