from __future__ import annotations

import streamlit as st
from openai import OpenAI
from openai import (
    RateLimitError,
    AuthenticationError,
    APIConnectionError,
    BadRequestError,
)


def _get_client() -> OpenAI:
    api_key = st.secrets.get("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY não encontrado no secrets.toml")
    return OpenAI(api_key=api_key)


client = _get_client()
MODEL_CHAT = st.secrets.get("MODEL_CHAT", "gpt-5-nano")

SYSTEM_PROMPT = (
    "Você é o MAIC — Monitoramento e Avaliação de Indicadores e Custos — uma Inteligência Artificial "
    "de apoio à gestão do SUS no Distrito Federal. Você foi desenvolvido pela Diretoria de Monitoramento "
    "e Avaliação da Secretaria de Saúde do DF. "
    "Seu objetivo é aumentar a eficiência da análise e da tomada de decisão de gestoras e gestores de saúde "
    "do DF, combinando respostas conversacionais com evidências: dados, indicadores, custos e informações internas "
    "disponibilizadas pela Diretoria. "
    "Você NÃO é uma central de atendimento ao cidadão e NÃO faz triagem clínica. Se houver pedido clínico/pessoal "
    "ou emergência, oriente a buscar os canais oficiais apropriados sem inventar condutas. "
    "Priorize sempre: (1) clareza, (2) objetividade, (3) utilidade para decisão. "
    "Quando a pergunta for de gestão, responda no formato: "
    "Contexto (1 frase) → Achados/leituras (bullets curtos) → Recomendações práticas (bullets) → "
    "Próximas visualizações no sistema (gráfico/mapa/tabela, se fizer sentido). "
    "Se faltar contexto, faça no máximo 1 pergunta objetiva (ex.: período, Região de Saúde/RA, indicador/custo). "
    "Nunca afirme que consultou dados internos se eles não foram fornecidos ao sistema; quando não houver dado, "
    "deixe explícito e sugira qual fonte interna precisa ser conectada. "
    "Responda sempre em português do Brasil, com frases curtas e sem enrolação."
)


def chat_reply(
    user_text: str,
    history: list[dict] | None = None,
    *,
    context_hint: str | None = None,
) -> str:
    """
    context_hint: opcional para injetar contexto do app (ex.: filtros da sidebar, ambiente, etc.)
    """
    context = ""
    if history:
        tail = history[-12:]
        context = "\n".join([f"{m['role']}: {m['content']}" for m in tail]) + "\n"

    if context_hint:
        context = f"contexto_do_sistema: {context_hint}\n" + context

    try:
        resp = client.responses.create(
            model=MODEL_CHAT,
            instructions=SYSTEM_PROMPT,
            input=f"{context}user: {user_text}",
            store=False,
        )
        return resp.output_text

    except AuthenticationError:
        return "Chave inválida/sem permissão. Confira OPENAI_API_KEY no secrets.toml."

    except RateLimitError:
        return (
            "Sem quota/crédito na API (erro 429). "
            "Você precisa ativar billing/adicionar créditos no OpenAI Platform para este projeto."
        )

    except APIConnectionError:
        return "Falha de conexão com a OpenAI (rede/proxy). Tente novamente."

    except BadRequestError as e:
        return f"Requisição inválida (modelo/parâmetros). Detalhe: {str(e)[:180]}"

    except Exception as e:
        return f"Erro inesperado ao chamar a IA: {str(e)[:180]}"

