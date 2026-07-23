import streamlit as st
import pandas as pd
from app.services.mapping_service import MappingService
from app.services.validation_service import validate_sku_df

st.set_page_config(page_title="Качество данных", layout="wide")
st.title("🧪 Качество данных")

sku_file = st.session_state.get("sku_file")
if not sku_file:
    st.warning("SKU-файл пока не загружен.")
else:
    df = pd.read_excel(sku_file)
    ms = MappingService()
    mapping = ms.auto_map(df.columns)
    st.subheader("Автоматический маппинг")
    st.json(mapping)
    mapped = ms.apply_mapping(df, mapping)
    issues = validate_sku_df(mapped)
    st.subheader("Проблемы качества")
    if not issues:
        st.success("Критичных проблем не найдено")
    else:
        st.dataframe(pd.DataFrame(issues, columns=["severity", "message", "column"]), use_container_width=True)
    st.subheader("Превью данных")
    st.dataframe(mapped.head(20), use_container_width=True)
