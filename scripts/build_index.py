from __future__ import annotations
import json
from pathlib import Path

from core.config import settings
from ingest.index_docs import build_index
from ingest.drive_client import list_pdfs, read_pdf_bytes
from ingest.pdf_reader import extract

def main():
    docs = []
    # Indexa PDFs (modo LOCAL). Se não houver PDFs, indexa textos exemplo.
    pdfs = list_pdfs()
    for ref in pdfs:
        pdf_bytes = read_pdf_bytes(ref)
        doc = extract(pdf_bytes, doc_id=ref.doc_id, name=ref.name)
        docs.append({"doc_id": doc.doc_id, "name": doc.name, "text": doc.text})

    # fallback: arquivo exemplo
    sample_txt = Path("assets/data/sample/boletim_exemplo.txt")
    if sample_txt.exists() and not docs:
        docs.append({"doc_id": "sample_boletim", "name": sample_txt.name, "text": sample_txt.read_text(encoding="utf-8")})

    build_index(docs, settings.DOC_INDEX_PATH)
    print(f"OK: índice gerado em {settings.DOC_INDEX_PATH} com {len(docs)} documento(s).")

if __name__ == "__main__":
    main()
