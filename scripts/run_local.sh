#!/usr/bin/env bash
set -euo pipefail
pip install -r requirements.txt
streamlit run streamlit_app.py
