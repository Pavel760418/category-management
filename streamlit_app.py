"""
Точка входа для Streamlit Community Cloud.

Cloud по умолчанию ищет именно `streamlit_app.py` в корне репозитория.
Локальный запуск: `streamlit run streamlit_app.py`
"""

from pathlib import Path
import sys

# Гарантируем импорт пакета `app` из корня репозитория
ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import streamlit as st

from app.home_page import render_home

st.set_page_config(page_title="Category Management BI", layout="wide")
render_home()
