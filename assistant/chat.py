from __future__ import annotations
import pandas as pd
from assistant.intents import infer_intent
from data.pipeline import load_cases_dataset
from viz.tabelas import tabela_resumo

def respond(message: str, filters: dict) -> dict:
    intent = infer_intent(message)
    df = load_cases_dataset(filters)

    # recorte por período (últimas N semanas)
    n = int(filters.get("periodo_semanas", 16))
    if len(df) > 0:
        df = df.sort_values("data_ref").groupby("regiao_saude", as_index=False).tail(n)

    if intent == "tabela":
        tab = tabela_resumo(df)
        texto = (
            f"Resumo de {filters.get('agravo')} para "
            f"{filters.get('regiao_saude','Todas')} nas últimas {n} semanas: "
            f"{int(tab['casos'].sum())} casos no total."
        )
        return {"text": texto, "view": "tabela", "data": {"table": tab}}

    if intent == "grafico":
        texto = (
            f"Vou te mostrar a série semanal de incidência de {filters.get('agravo')} "
            f"nas últimas {n} semanas. Se quiser, eu faço também ranking de casos."
        )
        return {"text": texto, "view": "grafico", "data": {"df": df}}

    if intent == "mapa":
        texto = "Mapa de pontos de serviços (exemplo). Para choropleth real, pluga limites (RS/RA/Município) no geo/."
        return {"text": texto, "view": "mapa", "data": {}}

    if intent == "docs":
        texto = "Posso buscar trechos nos PDFs indexados. Abra a aba Documentos (PDF) para consultar."
        return {"text": texto, "view": "docs", "data": {}}

    # Geral
    texto = (
        f"Entendi. No MVP eu consigo: (1) série de incidência, (2) ranking de casos, (3) mapa de serviços, "
        f"(4) consulta a PDFs indexados. Diga: 'gráfico', 'tabela', 'mapa' ou 'pdf'."
    )
    return {"text": texto, "view": "geral", "data": {"df": df}}
