from __future__ import annotations
from ui.layout import set_page, load_css, header
from core.logging import setup_logging

import streamlit as st

logger = setup_logging()

def main():
    set_page()
    load_css("assets/style.css")
    header()

    st.info("Use o menu lateral do Streamlit para navegar entre as páginas (Chat, Dashboard, Mapas, Tabelas, PDFs).")

if __name__ == "__main__":
    main()
