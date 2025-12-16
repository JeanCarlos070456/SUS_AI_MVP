from __future__ import annotations
import streamlit as st
from core.config import settings

def set_page():
    st.set_page_config(
        page_title=settings.APP_TITLE,
        page_icon="🧠",
        layout="wide",
        initial_sidebar_state="expanded",
    )

def load_css(path: str = "assets/style.css"):
    try:
        with open(path, "r", encoding="utf-8") as f:
            css = f.read()
        st.markdown(f"<style>{css}</style>", unsafe_allow_html=True)
    except Exception:
        pass

def header():
    st.markdown(f"## {settings.APP_TITLE}")
    if settings.APP_SUBTITLE:
        st.caption(settings.APP_SUBTITLE)
