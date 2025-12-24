from __future__ import annotations
import streamlit as st
from ui.layout import header
from ui.sidebar import get_filters
from core.config import settings
from ingest.drive_client import list_pdfs, read_pdf_bytes
from ingest.pdf_reader import extract
from ingest.index_docs import search

header()
filters = get_filters()

st.markdown("### Documentos (PDF) — MVP")
st.caption("Modo LOCAL: coloque PDFs em assets/docs/. Para indexar, rode: `python scripts/build_index.py`.")

colA, colB = st.columns([1,2])
with colA:
    pdfs = list_pdfs()
    names = ["(nenhum)"] + [p.name for p in pdfs]
    pick = st.selectbox("PDFs disponíveis", names, index=0)

with colB:
    q = st.text_input("Buscar no índice", placeholder="ex: incidencia dengue regiao oeste")
    if st.button("Buscar"):
        try:
            hits = search(settings.DOC_INDEX_PATH, q, top_k=5)
            if not hits:
                st.info("Nada encontrado. Gere o índice ou refine a consulta.")
            else:
                for h in hits:
                    with st.expander(f"{h['name']} | score={h['score']} | {h['chunk_id']}"):
                        st.write(h["text"])
        except Exception as e:
            st.error(f"Erro na busca: {e}")

st.markdown("---")
st.markdown("#### Pré-visualizar texto extraído (primeiro PDF)")
if pick != "(nenhum)":
    ref = next((p for p in pdfs if p.name == pick), None)
    if ref:
        try:
            pdf_bytes = read_pdf_bytes(ref)
            doc = extract(pdf_bytes, doc_id=ref.doc_id, name=ref.name)
            st.write(f"Engine: {doc.meta.get('engine')}")
            st.text_area("Texto extraído (trecho)", value=doc.text[:6000], height=260)
        except Exception as e:
            st.error(f"Falha ao ler PDF: {e}")
