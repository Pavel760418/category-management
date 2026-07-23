import streamlit as st
import pandas as pd

from app.services.mapping_service import MappingService
from app.services.schema_service import get_schema_service
from app.services.validation_service import validate_sku_df
from app.utils.io import read_template_excel

st.set_page_config(page_title="Качество данных", layout="wide")
st.title("🧪 Качество данных")

schema = get_schema_service()
sku_file = st.session_state.get("sku_file")
if not sku_file:
    st.warning("Файл данных SKU пока не загружен. Перейдите в раздел «Загрузка данных».")
else:
    df = st.session_state.get("mapped_df_sku")
    mapping = st.session_state.get("mapping_sku")
    ms = MappingService(schema)

    if df is None:
        raw = read_template_excel(sku_file, "sku")
        mapping = ms.auto_map(raw.columns, template_key="sku")
        df = ms.apply_mapping(raw, mapping)

    st.subheader("Автоматический маппинг")
    st.caption("Показаны русские названия полей системы → колонки загруженного файла.")
    st.json(ms.mapping_for_ui(mapping or {}))

    missing = ms.unmapped_required(mapping or {}, "sku")
    if missing:
        st.error("Не хватает обязательных полей: " + ", ".join(missing))

    issues = validate_sku_df(df, schema)
    st.subheader("Проблемы качества")
    if not issues:
        st.success("Критичных проблем не найдено")
    else:
        view = pd.DataFrame(issues, columns=["уровень", "сообщение", "колонка"])
        st.dataframe(view, use_container_width=True)

    st.subheader("Превью данных")
    # для превью показываем русские заголовки, не трогая внутренний df
    display_df = df.head(20).rename(columns=schema.display_map(list(df.columns)))
    st.dataframe(display_df, use_container_width=True)
