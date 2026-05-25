from __future__ import annotations

import io
import json
from typing import Iterable

import streamlit as st
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload


SCOPES = [
    "https://www.googleapis.com/auth/drive.readonly",
    "https://www.googleapis.com/auth/spreadsheets.readonly",
]


def _service_account_info() -> dict:
    """
    Lê o JSON inteiro da Service Account a partir do secrets.toml.

    Suporta:
      - GCP_SERVICE_ACCOUNT_JSON (recomendado)
      - GOOGLE_SERVICE_ACCOUNT (compat)
    """
    raw = (st.secrets.get("GCP_SERVICE_ACCOUNT_JSON") or st.secrets.get("GOOGLE_SERVICE_ACCOUNT") or "").strip()
    if not raw:
        raise RuntimeError(
            "Service Account não encontrada no secrets.toml. "
            "Defina GCP_SERVICE_ACCOUNT_JSON com o JSON inteiro (string multilinha)."
        )

    try:
        return json.loads(raw)
    except Exception as e:
        raise RuntimeError(
            "GCP_SERVICE_ACCOUNT_JSON não é um JSON válido. "
            "Cole o JSON inteiro da service account (com chaves, aspas e private_key com \\n)."
        ) from e


def _creds() -> Credentials:
    info = _service_account_info()
    return Credentials.from_service_account_info(info, scopes=SCOPES)


def drive_client():
    return build("drive", "v3", credentials=_creds(), cache_discovery=False)


def sheets_client():
    return build("sheets", "v4", credentials=_creds(), cache_discovery=False)


def list_shared_drives(page_size: int = 100) -> list[dict]:
    """
    Lista Shared Drives visíveis para a Service Account.
    Requer que a Service Account tenha acesso ao Shared Drive.
    """
    svc = drive_client()
    resp = svc.drives().list(
        pageSize=page_size,
        fields="drives(id,name)",
        useDomainAdminAccess=False,
    ).execute()
    return resp.get("drives", [])


def list_files_in_folder(
    folder_id: str,
    shared_drive_id: str | None = None,
    mime_types: Iterable[str] | None = None,
    mime_contains: str | None = None,
    page_size: int = 200,
) -> list[dict]:
    """
    Lista arquivos dentro de uma pasta.

    - shared_drive_id: se a pasta estiver dentro de um Shared Drive, passar ajuda (corpora=drive).
    - mime_types: filtra por lista EXATA de mimeTypes (OR).
    - mime_contains: filtro parcial (contains) — útil, mas menos preciso que mime_types.
    """
    svc = drive_client()

    q_parts = [f"'{folder_id}' in parents", "trashed = false"]

    if mime_types:
        m = " or ".join([f"mimeType='{mt}'" for mt in mime_types])
        q_parts.append(f"({m})")
    elif mime_contains:
        q_parts.append(f"mimeType contains '{mime_contains}'")

    q = " and ".join(q_parts)

    params = {
        "q": q,
        "fields": "files(id,name,mimeType,modifiedTime,size,owners(displayName,emailAddress))",
        "pageSize": page_size,
        "supportsAllDrives": True,
        "includeItemsFromAllDrives": True,
    }

    if shared_drive_id:
        params.update(
            {
                "corpora": "drive",
                "driveId": shared_drive_id,
            }
        )

    resp = svc.files().list(**params).execute()
    return resp.get("files", [])


def download_file(file_id: str) -> bytes:
    """
    Baixa bytes de um arquivo normal (PDF, CSV, etc).
    Para arquivos nativos Google Docs/Sheets/Slides, use export_google_file().
    """
    svc = drive_client()
    request = svc.files().get_media(fileId=file_id, supportsAllDrives=True)
    fh = io.BytesIO()
    downloader = MediaIoBaseDownload(fh, request)
    done = False
    while not done:
        _, done = downloader.next_chunk()
    return fh.getvalue()


# Compat (se você já usa esse nome em algum lugar)
download_file_bytes = download_file


def export_google_file(file_id: str, export_mime: str) -> bytes:
    """
    Exporta arquivos nativos do Google:
      - Docs/Sheets/Slides -> pdf/csv/txt etc (dependendo do tipo)

    Ex:
      export_mime="application/pdf"
      export_mime="text/plain"
      export_mime="text/csv"
    """
    svc = drive_client()
    request = svc.files().export_media(fileId=file_id, mimeType=export_mime)
    fh = io.BytesIO()
    downloader = MediaIoBaseDownload(fh, request)
    done = False
    while not done:
        _, done = downloader.next_chunk()
    return fh.getvalue()


def read_sheet_values(spreadsheet_id: str, range_a1: str):
    svc = sheets_client()
    resp = svc.spreadsheets().values().get(
        spreadsheetId=spreadsheet_id,
        range=range_a1,
    ).execute()
    return resp.get("values", [])
