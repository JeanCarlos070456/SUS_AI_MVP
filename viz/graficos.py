from __future__ import annotations
import plotly.express as px
import pandas as pd

def serie_incidencia(df: pd.DataFrame):
    fig = px.line(
        df,
        x="data_ref",
        y="incidencia_100k",
        color="regiao_saude",
        markers=True,
        title="Incidência (por 100 mil) - Série semanal",
        labels={"data_ref":"Data (semana)", "incidencia_100k":"Incidência/100k", "regiao_saude":"Região de Saúde"},
    )
    fig.update_layout(legend_title_text="Região de Saúde", height=420, margin=dict(l=10,r=10,t=50,b=10))
    return fig

def ranking_casos(df: pd.DataFrame):
    g = df.groupby("regiao_saude", as_index=False)["casos"].sum().sort_values("casos", ascending=False)
    fig = px.bar(
        g,
        x="regiao_saude",
        y="casos",
        title="Casos acumulados (período selecionado)",
        labels={"regiao_saude":"Região de Saúde", "casos":"Casos"},
    )
    fig.update_layout(height=420, margin=dict(l=10,r=10,t=50,b=10))
    return fig
