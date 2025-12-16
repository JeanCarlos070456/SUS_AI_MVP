from __future__ import annotations
import streamlit as st
from ui.layout import header
from ui.sidebar import get_filters
from assistant.chat import respond
from assistant.memory import get_history, add_message

header()
filters = get_filters()

st.markdown("### Chat operacional (MVP)")
hist = get_history()
for m in hist:
    with st.chat_message(m["role"]):
        st.markdown(m["content"])

msg = st.chat_input("Pergunte algo: ex. 'gráfico de dengue', 'tabela', 'mapa', 'pdf'")
if msg:
    add_message("user", msg)
    out = respond(msg, filters)
    add_message("assistant", out["text"])
    st.rerun()
