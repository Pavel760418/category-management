import streamlit as st

from app.services.schema_service import get_schema_service


def render_upload_help():
    st.info(
        "Загрузите один или несколько Excel-файлов по русскоязычным шаблонам. "
        "Система автоматически сопоставит колонки, покажет проблемы качества данных "
        "и рассчитает только те блоки, для которых хватает информации."
    )


def render_template_field_guide(template_key: str):
    """Показать обязательные и необязательные поля шаблона на русском."""
    schema = get_schema_service()
    tpl = schema.template(template_key)
    st.markdown(f"**{tpl['title_ru']}**")
    st.caption(tpl.get("description_ru", ""))

    req = [schema.display_name(f) for f in tpl["required_fields"]]
    opt = [schema.display_name(f) for f in tpl.get("optional_fields") or []]

    c1, c2 = st.columns(2)
    with c1:
        st.markdown("Обязательные поля")
        for name in req:
            st.markdown(f"- {name}")
    with c2:
        st.markdown("Необязательные поля")
        if opt:
            for name in opt:
                st.markdown(f"- {name}")
        else:
            st.caption("Нет необязательных полей")
