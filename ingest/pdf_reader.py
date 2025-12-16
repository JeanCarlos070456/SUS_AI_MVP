from __future__ import annotations
from dataclasses import dataclass
from typing import Any
import io

from core.errors import ParseError

@dataclass
class Document:
    doc_id: str
    name: str
    text: str
    tables: list
    meta: dict

def extract(pdf_bytes: bytes, *, doc_id: str, name: str) -> Document:
    text = ""
    tables = []
    meta = {"engine": None}

    # prefer pdfplumber
    try:
        import pdfplumber  # type: ignore
        meta["engine"] = "pdfplumber"
        with pdfplumber.open(io.BytesIO(pdf_bytes)) as pdf:
            for page in pdf.pages:
                text += (page.extract_text() or "") + "\n"
                # extração de tabelas simples (nem sempre funciona)
                try:
                    tbl = page.extract_table()
                    if tbl:
                        tables.append(tbl)
                except Exception:
                    pass
    except Exception:
        # fallback pypdf
        try:
            from pypdf import PdfReader  # type: ignore
            meta["engine"] = "pypdf"
            reader = PdfReader(io.BytesIO(pdf_bytes))
            for page in reader.pages:
                text += (page.extract_text() or "") + "\n"
        except Exception as e:
            raise ParseError(f"Falha ao extrair PDF: {e}") from e

    return Document(doc_id=doc_id, name=name, text=text, tables=tables, meta=meta)
