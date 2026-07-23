import streamlit as st


def render_kpi_cards(kpi_df):
    cols = st.columns(4)
    for idx, (_, row) in enumerate(kpi_df.iterrows()):
        with cols[idx % 4]:
            st.metric(label=row["name"], value=_fmt(row["actual"]), delta=row["status"])


def _fmt(v):
    if v is None:
        return "н/д"
    try:
        if abs(float(v)) >= 1000:
            return f"{float(v):,.0f}".replace(",", " ")
        return f"{float(v):.2f}"
    except Exception:
        return str(v)
