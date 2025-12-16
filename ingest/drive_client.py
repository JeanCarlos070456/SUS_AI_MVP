from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

from core.config import settings
from core.errors import DataSourceError

@dataclass
class DocRef:
    doc_id: str
    name: str
    path: str

def list_pdfs() -> list[DocRef]:
    mode = (settings.DRIVE_MODE or "LOCAL").upper()
    if mode == "LOCAL":
        root = Path(settings.LOCAL_DOCS_DIR)
        root.mkdir(parents=True, exist_ok=True)
        out: list[DocRef] = []
        for p in sorted(root.glob("*.pdf")):
            out.append(DocRef(doc_id=p.name, name=p.name, path=str(p)))
        return out

    # GDRIVE: deixamos stub (pra evitar dependência/credencial no MVP zipado)
    raise DataSourceError(
        "DRIVE_MODE=GDRIVE ainda não está configurado neste MVP. "
        "Use DRIVE_MODE=LOCAL e coloque PDFs em assets/docs/. "
        "Depois você pluga google-api-python-client aqui."
    )

def read_pdf_bytes(doc: DocRef) -> bytes:
    if settings.DRIVE_MODE.upper() != "LOCAL":
        raise DataSourceError("Leitura de bytes suportada no MVP apenas no modo LOCAL.")
    p = Path(doc.path)
    return p.read_bytes()
