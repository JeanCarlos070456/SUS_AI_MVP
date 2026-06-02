from __future__ import annotations

from typing import Any

from assistant.intents import infer_intent
from assistant.memory import get_history
from data.pipeline import load_cases_dataset
from services.llm import chat_reply
from viz.tabelas import tabela_resumo


INSTITUTIONAL_FALLBACK_KEYWORDS = {
    "maic",
    "monitoramento",
    "avaliação",
    "avaliacao",
    "indicador",
    "indicadores",
    "custo",
    "custos",
    "imd",
    "rgqc",
    "apura",
    "apurasus",
    "produção",
    "producao",
    "gemag",
    "gemap",
    "gemac",
    "dimoas",
    "acordo",
    "acordos",
    "pds",
    "pas",
    "rdqa",
    "região",
    "regiao",
    "srs",
    "unidade",
    "unidades",
    "hospital",
    "hospitais",
    "policlinica",
    "policlínica",
}


def _safe_filters(filters: dict | None) -> dict:
    return filters if isinstance(filters, dict) else {}


def _normalize_text(text: str) -> str:
    return (text or "").strip().lower()


def _fallback_requires_drive(message: str) -> bool:
    """
    Fallback local caso services.drive_catalog ainda não esteja importável.
    Não substitui o classificador oficial, só evita deixar pergunta institucional cair no LLM.
    """
    text = _normalize_text(message)

    if not text:
        return False

    return any(keyword in text for keyword in INSTITUTIONAL_FALLBACK_KEYWORDS)


def _requires_drive_source(message: str) -> bool:
    """
    Decide se a pergunta precisa obrigatoriamente usar fonte institucional do Drive.

    Regra:
    - Perguntas sobre monitoramento, indicadores, custos, IMD, RGQC, ApuraSUS,
      regiões/unidades e instrumentos institucionais devem ir para o Drive.
    - Perguntas conceituais/genéricas podem ir para o LLM.
    """
    try:
        from services.drive_catalog import is_institutional_analytics_question

        return bool(is_institutional_analytics_question(message))
    except Exception:
        return _fallback_requires_drive(message)


def _answer_from_drive(message: str) -> dict:
    """
    Rota institucional segura.

    Importante:
    Se der erro aqui, NÃO cai automaticamente no ChatGPT.
    Pergunta institucional sem Drive não deve virar resposta inventada.
    """
    try:
        from services.drive_analytics import analyze_question_from_drive

        result = analyze_question_from_drive(
            message,
            catalog_limit=12,
            selected_limit=1,
            max_sheets=12,
            preview_rows=5,
            pdf_pages=5,
            max_scan_rows=140,
            max_scan_cols=45,
            require_institutional_question=False,
        )

        text = str(result.get("text") or "").strip()

        if not text:
            text = (
                "A pergunta foi classificada como institucional, mas não consegui gerar "
                "uma resposta com base no Drive. Atualize o catálogo com "
                "`python scripts/test_gdrive.py` e tente novamente."
            )

        return {
            "text": text,
            "view": "drive_analytics",
            "data": result,
        }

    except Exception as e:
        return {
            "text": (
                "A pergunta exige fonte institucional do Drive, mas ocorreu uma falha "
                "ao acionar a camada `drive_analytics.py`. "
                "Não vou responder com base genérica para evitar informação sem evidência.\n\n"
                f"Erro técnico: {str(e)[:300]}"
            ),
            "view": "drive_analytics_error",
            "data": {"error": repr(e)},
        }


def _load_filtered_cases(filters: dict) -> tuple[Any, int]:
    """
    Mantém o fluxo antigo para tabela/gráfico/mapa, mas só carrega dataset
    quando essa rota realmente for usada.
    """
    n = int(filters.get("periodo_semanas", 16) or 16)
    df = load_cases_dataset(filters)

    if len(df) > 0:
        df = df.sort_values("data_ref").groupby("regiao_saude", as_index=False).tail(n)

    return df, n


def _build_context_hint(filters: dict) -> str:
    """
    Contexto leve para resposta geral do LLM.
    Não injeta dados institucionais.
    """
    if not filters:
        return ""

    useful_keys = [
        "agravo",
        "regiao_saude",
        "periodo_semanas",
        "ano",
        "mes",
    ]

    parts = []
    for key in useful_keys:
        value = filters.get(key)
        if value not in [None, "", "Todas", "Todos"]:
            parts.append(f"{key}={value}")

    return "; ".join(parts)


def respond(message: str, filters: dict | None) -> dict:
    """
    Orquestrador principal do chat do MAIC.

    Regras:
    1. Pergunta institucional/analítica usa Drive obrigatoriamente.
    2. Pergunta visual antiga mantém tabela/gráfico/mapa com dataset do app.
    3. Pergunta geral usa LLM.
    """
    filters = _safe_filters(filters)
    message = (message or "").strip()

    if not message:
        return {
            "text": "Digite uma pergunta para o MAIC analisar.",
            "view": "geral",
            "data": {},
        }

    intent = infer_intent(message)

    # 1) Governança institucional: antes de qualquer resposta genérica.
    # Tudo que for monitoramento, indicadores, custos, IMD, RGQC, ApuraSUS etc. vai para Drive.
    if _requires_drive_source(message):
        return _answer_from_drive(message)

    # 2) Fluxo visual antigo preservado para comandos não institucionais.
    if intent == "tabela":
        df, n = _load_filtered_cases(filters)
        tab = tabela_resumo(df)

        texto = (
            f"Resumo de {filters.get('agravo')} para "
            f"{filters.get('regiao_saude', 'Todas')} nas últimas {n} semanas: "
            f"{int(tab['casos'].sum())} casos no total."
        )

        return {
            "text": texto,
            "view": "tabela",
            "data": {"table": tab},
        }

    if intent == "grafico":
        df, n = _load_filtered_cases(filters)

        texto = (
            f"Vou te mostrar a série semanal de incidência de {filters.get('agravo')} "
            f"nas últimas {n} semanas. Se quiser, eu faço também ranking de casos."
        )

        return {
            "text": texto,
            "view": "grafico",
            "data": {"df": df},
        }

    if intent == "mapa":
        texto = (
            "Mapa de pontos de serviços. Para análise institucional por região, "
            "indicadores ou custos, faça uma pergunta analítica que eu consulto o Drive."
        )

        return {
            "text": texto,
            "view": "mapa",
            "data": {},
        }

    if intent == "docs":
        texto = (
            "Para documentos institucionais do MAIC, pergunte pelo tema, ano, região, "
            "indicador ou custo. Exemplo: `RGQC região norte 2025` ou "
            "`custos IMD 2024 região oeste`."
        )

        return {
            "text": texto,
            "view": "docs",
            "data": {},
        }

    # 3) Pergunta geral: liberada para ChatGPT.
    hist = get_history()
    context_hint = _build_context_hint(filters)

    texto = chat_reply(
        message,
        history=hist,
        context_hint=context_hint or None,
    )

    return {
        "text": texto,
        "view": "geral",
        "data": {},
    }