from __future__ import annotations
import pandas as pd
from ingest.pdf_reader import Document

def parse(doc: Document) -> pd.DataFrame:
    # MVP: parser demonstrativo.
    # Você vai implementar regras reais (regex/tabelas) conforme o padrão do boletim.
    # Aqui vamos só achar linhas com 'casos' e extrair números, de forma simplista.
    text = doc.text.lower()
    total = 0
    for token in text.split():
        if token.isdigit():
            total += int(token)
            break
    return pd.DataFrame([{
        "doc_id": doc.doc_id,
        "name": doc.name,
        "metric": "casos_mencionados_primeiro_numero",
        "value": total,
        "engine": doc.meta.get("engine"),
    }])
