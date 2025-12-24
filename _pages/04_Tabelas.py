from __future__ import annotations
import streamlit as st
from ui.layout import header
from ui.sidebar import get_filters
from data.pipeline import load_cases_dataset
from viz.tabelas import tabela_resumo

header()
filters = get_filters()
df = load_cases_dataset(filters)

n = int(filters.get("periodo_semanas", 16))
df = df.sort_values("data_ref").groupby("regiao_saude", as_index=False).tail(n)

tab = tabela_resumo(df)
st.dataframe(tab, use_container_width=True)

csv = tab.to_csv(index=False).encode("utf-8")
st.download_button("Baixar CSV", data=csv, file_name="resumo.csv", mime="text/csv")
