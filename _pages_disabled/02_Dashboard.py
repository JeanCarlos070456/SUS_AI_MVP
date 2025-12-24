from __future__ import annotations
import streamlit as st
from ui.layout import header
from ui.sidebar import get_filters
from data.pipeline import load_cases_dataset
from viz.graficos import serie_incidencia, ranking_casos
from viz.tabelas import tabela_resumo

header()
filters = get_filters()
df = load_cases_dataset(filters)

# recorte por período
n = int(filters.get("periodo_semanas", 16))
df = df.sort_values("data_ref").groupby("regiao_saude", as_index=False).tail(n)

c1, c2, c3 = st.columns(3)
c1.metric("Agravo", filters.get("agravo"))
c2.metric("Região de Saúde", filters.get("regiao_saude"))
c3.metric("Semanas", n)

st.plotly_chart(serie_incidencia(df), use_container_width=True)
st.plotly_chart(ranking_casos(df), use_container_width=True)

st.markdown("### Tabela resumo")
st.dataframe(tabela_resumo(df), use_container_width=True)
