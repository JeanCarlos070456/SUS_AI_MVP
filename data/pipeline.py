from __future__ import annotations
import pandas as pd
from services import apis
from data.metrics import add_incidencia

def load_cases_dataset(filters: dict) -> pd.DataFrame:
    df = apis.get_cases(filters)
    df["data_ref"] = pd.to_datetime(df["data_ref"])
    df = add_incidencia(df)
    # Filtros mínimos
    reg = filters.get("regiao_saude")
    if reg and reg != "Todas":
        df = df[df["regiao_saude"] == reg]
    return df.sort_values(["ano","semana","regiao_saude"]).reset_index(drop=True)

def load_points_dataset(filters: dict) -> pd.DataFrame:
    df = apis.get_services_points(filters)
    reg = filters.get("regiao_saude")
    if reg and reg != "Todas":
        df = df[df["regiao_saude"] == reg]
    return df.reset_index(drop=True)
