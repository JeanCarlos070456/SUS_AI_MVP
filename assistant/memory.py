from __future__ import annotations
import streamlit as st

KEY = "chat_history"

def get_history() -> list[dict]:
    if KEY not in st.session_state:
        st.session_state[KEY] = []
    return st.session_state[KEY]

def add_message(role: str, content: str):
    hist = get_history()
    hist.append({"role": role, "content": content})
