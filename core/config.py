from __future__ import annotations
import os
from dataclasses import dataclass

def _env(name: str, default: str | None = None) -> str | None:
    v = os.getenv(name)
    return v if v not in (None, "") else default

@dataclass(frozen=True)
class Settings:
    APP_TITLE: str = _env("APP_TITLE", "IA de Gestão Regionalizada do SUS") or "IA de Gestão Regionalizada do SUS"
    APP_SUBTITLE: str = _env("APP_SUBTITLE", "MVP Streamlit: Chat + Dashboards + Mapas + PDFs") or ""
    ENV: str = _env("ENV", "dev") or "dev"

    # Datasources (placeholders)
    SESDF_BASE_URL: str = _env("SESDF_BASE_URL", "https://www.saude.df.gov.br") or "https://www.saude.df.gov.br"
    GEOSERVER_URL: str = _env("GEOSERVER_URL", "https://geoserver01.saude.df.gov.br/geoserver") or ""
    GEOSERVER_WORKSPACE: str = _env("GEOSERVER_WORKSPACE", "mapas_df") or "mapas_df"

    # Ingest
    DRIVE_MODE: str = _env("DRIVE_MODE", "LOCAL") or "LOCAL"  # LOCAL | GDRIVE
    LOCAL_DOCS_DIR: str = _env("LOCAL_DOCS_DIR", "assets/docs") or "assets/docs"
    DOC_INDEX_PATH: str = _env("DOC_INDEX_PATH", "assets/data/index/doc_index.json") or "assets/data/index/doc_index.json"

    # Feature flags
    ENABLE_DOCS: bool = (_env("ENABLE_DOCS", "1") or "1") in ("1","true","True","yes","Y")
    ENABLE_DIAGNOSTICS: bool = (_env("ENABLE_DIAGNOSTICS", "1") or "1") in ("1","true","True","yes","Y")

settings = Settings()
