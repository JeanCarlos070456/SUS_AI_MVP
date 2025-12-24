from __future__ import annotations
import streamlit as st
from dataclasses import dataclass

@dataclass
class Filters:
    agravo: str
    regiao_saude: str
    periodo_semanas: int

def get_filters() -> dict:
    with st.sidebar:
        st.markdown("### Filtros")
        agravo = st.selectbox("Agravo/tema", ["Dengue", "Tuberculose", "Hanseníase"], index=0)
        regiao_saude = st.selectbox("Região de Saúde", ["Todas", "Central", "Sul", "Norte", "Oeste", "Leste"], index=0)
        periodo_semanas = st.slider("Período (semanas)", min_value=4, max_value=52, value=16, step=4)
        st.markdown("---")
        st.caption("Fonte: Mock (substituir por APIs reais)")
    return {
        "agravo": agravo,
        "regiao_saude": regiao_saude,
        "periodo_semanas": int(periodo_semanas),
    }
