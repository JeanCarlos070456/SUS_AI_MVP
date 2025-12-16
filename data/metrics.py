from __future__ import annotations
import pandas as pd

def add_incidencia(df: pd.DataFrame, casos_col: str = "casos", pop_col: str = "pop") -> pd.DataFrame:
    out = df.copy()
    out["incidencia_100k"] = (out[casos_col] / out[pop_col]) * 100000.0
    return out

def summarize(df: pd.DataFrame, group_cols: list[str]) -> pd.DataFrame:
    g = df.groupby(group_cols, dropna=False, as_index=False).agg(
        casos=("casos", "sum"),
        pop=("pop", "max"),
        incidencia_100k=("incidencia_100k", "mean"),
    )
    return g
