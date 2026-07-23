"""
Совместимая точка входа.

Предпочтительный entry point (в т.ч. Streamlit Cloud): `streamlit_app.py`.
Этот файл оставлен для обратной совместимости: `streamlit run app/main.py`.

Важно: multipage-страницы лежат в корневом каталоге `pages/` рядом с
`streamlit_app.py`. При запуске через `app/main.py` боковое меню страниц
может быть недоступно — используйте `streamlit run streamlit_app.py`.
"""

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import streamlit as st

from app.home_page import render_home

st.set_page_config(page_title="Category Management BI", layout="wide")
st.warning(
    "Рекомендуемый запуск: `streamlit run streamlit_app.py` "
    "(так работает деплой на Streamlit Cloud и боковое меню страниц)."
)
render_home()
