from __future__ import annotations
from core.utils import tokenize

def infer_intent(message: str) -> str:
    toks = set(tokenize(message))
    if any(t in toks for t in ["mapa", "mapas", "geográfico", "geografico", "folium"]):
        return "mapa"
    if any(t in toks for t in ["gráfico", "grafico", "série", "serie", "linha", "rank", "ranking", "barras"]):
        return "grafico"
    if any(t in toks for t in ["tabela", "tabelas", "resumo", "csv", "excel"]):
        return "tabela"
    if any(t in toks for t in ["pdf", "boletim", "documento", "relatório", "relatorio"]):
        return "docs"
    return "geral"
