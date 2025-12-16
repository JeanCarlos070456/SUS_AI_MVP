from __future__ import annotations
import pandas as pd

def tabela_resumo(df: pd.DataFrame) -> pd.DataFrame:
    g = df.groupby("regiao_saude", as_index=False).agg(
        casos=("casos","sum"),
        incidencia_media_100k=("incidencia_100k","mean"),
        semanas=("semana","nunique"),
    ).sort_values("casos", ascending=False)
    g["incidencia_media_100k"] = g["incidencia_media_100k"].round(2)
    return g
