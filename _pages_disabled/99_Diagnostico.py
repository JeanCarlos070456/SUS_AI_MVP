from __future__ import annotations
import streamlit as st
import platform
import sys
from ui.layout import header
from core.config import settings
from core.utils import now_iso

header()
st.markdown("### Diagnóstico")

c1, c2, c3 = st.columns(3)
c1.metric("ENV", settings.ENV)
c2.metric("Python", sys.version.split()[0])
c3.metric("Agora (UTC)", now_iso())

st.code({
    "DRIVE_MODE": settings.DRIVE_MODE,
    "LOCAL_DOCS_DIR": settings.LOCAL_DOCS_DIR,
    "DOC_INDEX_PATH": settings.DOC_INDEX_PATH,
}, language="json")

st.caption(f"Plataforma: {platform.platform()}")
