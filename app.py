"""Bulgarmetrics entrypoint: common layout and dynamic analysis dropdown."""
import streamlit as st
from core.registry import discover_analyses, load_analysis
from shared.theme import apply_theme

st.set_page_config(page_title="БулгарМетрикс", page_icon="📊", layout="centered")
apply_theme()
st.title("БулгарМетрикс")
try:
    analyses = discover_analyses()
except (ValueError, KeyError, OSError) as exc:
    st.error(f"Грешка в регистъра на анализите: {exc}")
    st.stop()
if not analyses:
    st.warning("Няма налични анализи.")
    st.stop()
selected = st.selectbox(
    "Анализ", options=analyses, format_func=lambda a: a.label,
    key="selected_analysis_v2",
)
try:
    render = load_analysis(selected)
except (ImportError, AttributeError, TypeError) as exc:
    st.error(f"Анализът не може да бъде зареден: {exc}")
    st.stop()
render()
