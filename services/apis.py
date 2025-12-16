from __future__ import annotations
import pandas as pd
import streamlit as st
from datetime import date, timedelta
from core.cache import cache_data
from core.utils import now_iso

# ---------------------------------------------------------------------
# MVP: fontes de dados MOCK (substituir por SINAN/CNES/IBGE/SES-DF/etc.)
# ---------------------------------------------------------------------

def _mock_cases(filters: dict) -> pd.DataFrame:
    # Gera uma série semanal fake (52 semanas) com regionalização simples
    # para o DF: Regiões de Saúde "Central", "Sul", "Norte", "Oeste", "Leste"
    regions = ["Central", "Sul", "Norte", "Oeste", "Leste"]
    today = date.today()
    start = today - timedelta(days=7*52)
    rows = []
    for w in range(52):
        dt = start + timedelta(days=7*w)
        for reg in regions:
            base = {"Central": 55, "Sul": 35, "Norte": 30, "Oeste": 40, "Leste": 28}[reg]
            noise = (hash((reg, w)) % 19) - 9
            cases = max(0, base + noise)
            pop = {"Central": 550000, "Sul": 420000, "Norte": 390000, "Oeste": 510000, "Leste": 360000}[reg]
            rows.append({
                "agravo": filters.get("agravo", "Dengue"),
                "regiao_saude": reg,
                "semana": int(dt.strftime("%V")),
                "ano": dt.year,
                "data_ref": dt,
                "casos": cases,
                "pop": pop,
                "updated_at": now_iso(),
                "source": "mock",
            })
    return pd.DataFrame(rows)

@cache_data(ttl=60*15, show_spinner=False)
def get_cases(filters: dict) -> pd.DataFrame:
    # No futuro: chamar APIs reais e normalizar colunas aqui ou no data/pipeline
    return _mock_cases(filters)

@cache_data(ttl=60*15, show_spinner=False)
def get_services_points(filters: dict) -> pd.DataFrame:
    # Pontos fake (serviços/UPA/UBS/CAPS etc.)
    pts = [
        ("UBS", "UBS Asa Norte", -15.765, -47.882, "Central"),
        ("UPA", "UPA Ceilândia", -15.826, -48.104, "Oeste"),
        ("CAPS", "CAPS Taguatinga", -15.833, -48.055, "Oeste"),
        ("UBS", "UBS Gama", -16.017, -48.064, "Sul"),
        ("UBS", "UBS Sobradinho", -15.652, -47.789, "Norte"),
        ("UPA", "UPA Paranoá", -15.780, -47.780, "Leste"),
    ]
    return pd.DataFrame([{
        "tipo": t, "nome": n, "lat": lat, "lon": lon, "regiao_saude": rs
    } for t,n,lat,lon,rs in pts])
