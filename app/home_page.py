"""Главная страница приложения (общая для Cloud и локального запуска)."""

from pathlib import Path

import streamlit as st

from app.services.schema_service import get_schema_service
from app.services.template_service import TemplateService
from app.utils.logger import setup_logger


def _project_root() -> Path:
    return Path(__file__).resolve().parents[1]


def inject_css() -> None:
    css_path = Path(__file__).resolve().parent / "styles" / "theme.css"
    if css_path.exists():
        st.markdown(f"<style>{css_path.read_text(encoding='utf-8')}</style>", unsafe_allow_html=True)


def render_home() -> None:
    setup_logger()
    inject_css()

    st.title("Category Management BI")
    st.caption(
        "Production-like BI-приложение для категорийного менеджмента, "
        "коммерческого директора и CEO."
    )

    st.markdown(
        """
### Что делает система
- загружает Excel-файлы по **русскоязычным** шаблонам;
- автоматически сопоставляет колонки (русские названия — основной вариант);
- валидирует данные и показывает ошибки качества на русском языке;
- строит управленческий BI-дашборд;
- экспортирует итоговый Excel в логике исходного инструмента.
"""
    )

    schema = get_schema_service()
    tpl_service = TemplateService(str(_project_root() / "app" / "templates"), schema=schema)
    created = tpl_service.create_all()

    st.subheader("Шаблоны загрузки")
    st.caption(
        "Все шаблоны для скачивания и заполнения — на русском языке: "
        "имена файлов, листы, колонки и инструкции."
    )

    for key, path in created.items():
        meta = schema.template(key)
        with open(path, "rb") as f:
            st.download_button(
                label=f"Скачать «{meta['file_name_ru']}»",
                data=f,
                file_name=meta["file_name_ru"],
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                key=f"dl_{key}",
                help=meta.get("description_ru", ""),
            )
        with st.expander(f"Поля шаблона «{meta['short_label_ru']}»", expanded=False):
            req = ", ".join(schema.display_name(f) for f in meta["required_fields"])
            opt = ", ".join(schema.display_name(f) for f in meta.get("optional_fields") or []) or "—"
            st.markdown(f"**Обязательные:** {req}")
            st.markdown(f"**Необязательные:** {opt}")

    st.info(
        "Навигация по приложению находится в левом меню страниц Streamlit. "
        "Начните с раздела «Загрузка данных»."
    )
