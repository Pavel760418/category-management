import streamlit as st
from pathlib import Path

from app.components.upload_help import render_upload_help, render_template_field_guide
from app.services.mapping_service import MappingService
from app.services.schema_service import get_schema_service
from app.services.template_service import TemplateService
from app.services.validation_service import validate_by_template, validate_sku_df
from app.utils.io import read_template_excel

st.set_page_config(page_title="Загрузка данных", layout="wide")
st.title("📥 Загрузка данных")
render_upload_help()

schema = get_schema_service()
ms = MappingService(schema)
tpl_service = TemplateService(
    str(Path(__file__).resolve().parents[1] / "app" / "templates"),
    schema=schema,
)
created = tpl_service.create_all()

st.subheader("Скачать шаблоны Excel")
st.caption("Имена файлов, листов и колонок — на русском языке.")

cols = st.columns(3)
for col, key in zip(cols, schema.template_keys()):
    meta = schema.template(key)
    path = created[key]
    with col:
        st.markdown(f"**{meta['short_label_ru']}**")
        st.caption(meta["description_ru"])
        with open(path, "rb") as f:
            st.download_button(
                label=f"Скачать {meta['file_name_ru']}",
                data=f,
                file_name=meta["file_name_ru"],
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                key=f"upload_dl_{key}",
            )

st.subheader("Описание полей шаблонов")
tabs = st.tabs([schema.template(k)["short_label_ru"] for k in schema.template_keys()])
for tab, key in zip(tabs, schema.template_keys()):
    with tab:
        render_template_field_guide(key)

st.subheader("Загрузка файлов")
upload_cols = st.columns(3)
uploaded = {}
for col, key in zip(upload_cols, schema.template_keys()):
    meta = schema.template(key)
    with col:
        uploaded[key] = st.file_uploader(
            meta["upload_label_ru"],
            type=["xlsx"],
            key=f"uploader_{key}",
            help=f"Лист: «{meta['sheet_name_ru']}». Обязательные поля: "
            + ", ".join(schema.display_name(f) for f in meta["required_fields"]),
        )

# session keys сохраняем для совместимости с другими страницами
st.session_state["sku_file"] = uploaded.get("sku")
st.session_state["comp_file"] = uploaded.get("competitor")
st.session_state["goals_file"] = uploaded.get("goals")

st.caption(
    "Если часть файлов не загружена, приложение продолжит работу и явно покажет ограничения анализа."
)

st.subheader("Автосопоставление и ручной маппинг")
st.caption(
    "Слева — исходные колонки файла, справа — русские названия полей системы. "
    "Внутри расчётов используются технические ключи, скрытые от пользователя."
)


def _render_mapping_block(template_key: str, file_obj):
    meta = schema.template(template_key)
    st.markdown(f"#### {meta['short_label_ru']}")
    if not file_obj:
        st.warning(f"Файл «{meta['short_label_ru']}» пока не загружен.")
        return None, None

    df = read_template_excel(file_obj, template_key)
    if df.empty:
        st.error("Не удалось прочитать файл. Проверьте формат Excel.")
        return None, None

    auto = ms.auto_map(df.columns, template_key=template_key)
    targets = ms.available_targets_ru(template_key)
    options = ["— не сопоставлено —"] + list(df.columns)

    st.markdown("Автоматическое сопоставление (русские названия полей):")
    st.json(ms.mapping_for_ui(auto))

    missing = ms.unmapped_required(auto, template_key)
    if missing:
        st.warning("Не сопоставлены обязательные поля: " + ", ".join(missing))
    else:
        st.success("Все обязательные поля сопоставлены автоматически.")

    st.markdown("Ручная корректировка маппинга")
    manual = {}
    for canon, label_ru in targets.items():
        default = auto.get(canon)
        default_idx = options.index(default) if default in options else 0
        chosen = st.selectbox(
            label_ru,
            options=options,
            index=default_idx,
            key=f"map_{template_key}_{canon}",
        )
        if chosen != "— не сопоставлено —":
            manual[canon] = chosen

    mapped_df = ms.apply_mapping(df, manual)
    if template_key == "sku":
        issues = validate_sku_df(mapped_df, schema)
    else:
        issues = validate_by_template(mapped_df, template_key, schema)

    if issues:
        for severity, message, _ in issues:
            if severity == "error":
                st.error(message)
            else:
                st.warning(message)
    else:
        st.success("Критических ошибок по обязательным полям нет.")

    st.dataframe(mapped_df.head(10), use_container_width=True)
    st.session_state[f"mapping_{template_key}"] = manual
    st.session_state[f"mapped_df_{template_key}"] = mapped_df
    return manual, mapped_df


for key in schema.template_keys():
    with st.expander(f"Маппинг: {schema.template(key)['short_label_ru']}", expanded=(key == "sku")):
        _render_mapping_block(key, uploaded.get(key))
