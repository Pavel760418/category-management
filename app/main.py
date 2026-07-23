import streamlit as st
from pathlib import Path
from app.services.template_service import TemplateService
from app.utils.logger import setup_logger

st.set_page_config(page_title="Category Management BI", layout="wide")
logger = setup_logger()

def inject_css():
    css_path = Path(__file__).resolve().parent / "styles" / "theme.css"
    if css_path.exists():
        st.markdown(f"<style>{css_path.read_text(encoding='utf-8')}</style>", unsafe_allow_html=True)

inject_css()

st.title("Category Management BI")
st.caption("Production-like BI-приложение для категорийного менеджмента, коммерческого директора и CEO.")

st.markdown("""
### Что делает система
- загружает Excel-файлы по шаблонам;
- автоматически сопоставляет колонки;
- валидирует данные и показывает ошибки качества;
- строит управленческий BI-дашборд;
- экспортирует итоговый Excel в логике исходного инструмента.
""")

tpl = TemplateService(str(Path(__file__).resolve().parent / "templates"))
sku = tpl.create_sku_template()
comp = tpl.create_competitor_template()
goals = tpl.create_goals_template()

st.subheader("Шаблоны загрузки")
for p in [sku, comp, goals]:
    with open(p, "rb") as f:
        st.download_button(f"Скачать {p.name}", data=f, file_name=p.name)

st.info("Навигация по приложению находится в левом меню страниц Streamlit.")
