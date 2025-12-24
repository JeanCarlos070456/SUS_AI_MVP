from __future__ import annotations

import platform
import sys
import base64  # para o fundo em PNG

import streamlit as st
from streamlit_folium import st_folium

from core.config import settings
from core.logging import setup_logging
from core.utils import now_iso
from ui.layout import set_page, load_css, header
from ui.sidebar import get_filters

from assistant.chat import respond
from assistant.memory import get_history, add_message

from data.pipeline import load_cases_dataset, load_points_dataset
from viz.graficos import serie_incidencia, ranking_casos
from viz.tabelas import tabela_resumo
from viz.mapas import mapa_pontos_servicos

from ingest.drive_client import list_pdfs, read_pdf_bytes
from ingest.pdf_reader import extract
from ingest.index_docs import search


logger = setup_logging()


def set_background():
    """
    Define o fundo global do app usando o PNG em style/fundo/fundo_painel.png,
    com camada suave por cima (opacidade controlada no linear-gradient).
    """
    img_path = "style/fundo/fundo_painel.png"
    try:
        with open(img_path, "rb") as f:
            data = base64.b64encode(f.read()).decode("utf-8")

        st.markdown(
            f"""
            <style>
            .stApp {{
                background-image:
                    linear-gradient(
                        rgba(246, 249, 247, 0.30),
                        rgba(246, 249, 247, 0.30)
                    ),
                    url("data:image/png;base64,{data}");
                background-size: cover;
                background-position: center;
                background-attachment: fixed;
            }}
            </style>
            """,
            unsafe_allow_html=True,
        )
    except FileNotFoundError:
        # Se o arquivo não existir, não quebra o app
        logger.warning("Imagem de fundo não encontrada em %s", img_path)


def tab_chat(filters: dict):
    st.markdown("### Chat operacional (MVP)")

    hist = get_history()
    for m in hist:
        with st.chat_message(m["role"]):
            st.markdown(m["content"])

    msg = st.chat_input("Pergunte algo: ex. 'gráfico', 'tabela', 'mapa', 'pdf'")
    if msg:
        add_message("user", msg)
        out = respond(msg, filters)
        add_message("assistant", out["text"])
        st.rerun()


def tab_dashboard(filters: dict):
    st.markdown("### Dashboard")
    df = load_cases_dataset(filters)

    n = int(filters.get("periodo_semanas", 16))
    df = df.sort_values("data_ref").groupby("regiao_saude", as_index=False).tail(n)

    c1, c2, c3 = st.columns(3)
    c1.metric("Agravo", filters.get("agravo"))
    c2.metric("Região de Saúde", filters.get("regiao_saude"))
    c3.metric("Semanas", n)

    st.plotly_chart(serie_incidencia(df), use_container_width=True)
    st.plotly_chart(ranking_casos(df), use_container_width=True)

    st.markdown("### Tabela resumo")
    st.dataframe(tabela_resumo(df), use_container_width=True)


def tab_mapas(filters: dict):
    st.markdown("### Mapas")
    pts = load_points_dataset(filters)
    m = mapa_pontos_servicos(pts)
    st_folium(m, width=None, height=600)


def tab_tabelas(filters: dict):
    st.markdown("### Tabelas")
    df = load_cases_dataset(filters)

    n = int(filters.get("periodo_semanas", 16))
    df = df.sort_values("data_ref").groupby("regiao_saude", as_index=False).tail(n)

    tab = tabela_resumo(df)
    st.dataframe(tab, use_container_width=True)

    csv = tab.to_csv(index=False).encode("utf-8")
    st.download_button("Baixar CSV", data=csv, file_name="resumo.csv", mime="text/csv")


def tab_docs():
    st.markdown("### Documentos (PDF)")
    st.caption(
        "Modo LOCAL: coloque PDFs em assets/docs/. "
        "Para indexar: `python scripts/build_index.py`."
    )

    colA, colB = st.columns([1, 2])
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
                        with st.expander(
                            f"{h['name']} | score={h['score']} | {h['chunk_id']}"
                        ):
                            st.write(h["text"])
            except Exception as e:
                st.error(f"Erro na busca: {e}")

    st.markdown("---")
    st.markdown("#### Pré-visualizar texto extraído")
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


def tab_diagnostico():
    st.markdown("### Diagnóstico")

    c1, c2, c3 = st.columns(3)
    c1.metric("ENV", settings.ENV)
    c2.metric("Python", sys.version.split()[0])
    c3.metric("Agora (UTC)", now_iso())

    st.code(
        {
            "DRIVE_MODE": settings.DRIVE_MODE,
            "LOCAL_DOCS_DIR": settings.LOCAL_DOCS_DIR,
            "DOC_INDEX_PATH": settings.DOC_INDEX_PATH,
        },
        language="json",
    )

    st.caption(f"Plataforma: {platform.platform()}")


def main():
    set_page()  # primeira chamada Streamlit
    set_background()  # aplica o fundo do painel
    load_css("assets/style.css")
    header()

    filters = get_filters()

    tabs = st.tabs(
        ["Chat", "Dashboard", "Mapas", "Tabelas", "Documentos PDF", "Diagnóstico"]
    )

    with tabs[0]:
        tab_chat(filters)
    with tabs[1]:
        tab_dashboard(filters)
    with tabs[2]:
        tab_mapas(filters)
    with tabs[3]:
        tab_tabelas(filters)
    with tabs[4]:
        tab_docs()
    with tabs[5]:
        tab_diagnostico()


if __name__ == "__main__":
    main()
