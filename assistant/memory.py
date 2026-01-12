from __future__ import annotations

import uuid
import streamlit as st


def _ensure_state():
    if "conversations" not in st.session_state:
        st.session_state["conversations"] = {}  # {cid: {"title": str, "messages": [..]}}
    if "active_conversation_id" not in st.session_state:
        st.session_state["active_conversation_id"] = None


def init_memory():
    _ensure_state()
    # Se não existir nenhuma conversa, cria uma default
    if not st.session_state["conversations"]:
        new_conversation("Novo chat")
    # Se o active estiver vazio/inválido, aponta pra primeira
    active = st.session_state.get("active_conversation_id")
    if active not in st.session_state["conversations"]:
        st.session_state["active_conversation_id"] = next(iter(st.session_state["conversations"].keys()))


def list_conversations():
    """
    Retorna lista [(cid, conv_dict), ...] em ordem de inserção.
    """
    _ensure_state()
    return list(st.session_state["conversations"].items())


def get_active_id() -> str:
    _ensure_state()
    return st.session_state.get("active_conversation_id")


def set_active(conversation_id: str):
    _ensure_state()
    if conversation_id in st.session_state["conversations"]:
        st.session_state["active_conversation_id"] = conversation_id


def new_conversation(title: str = "Novo chat") -> str:
    _ensure_state()
    cid = uuid.uuid4().hex[:10]
    st.session_state["conversations"][cid] = {
        "title": (title or "Sem título").strip(),
        "messages": [],
    }
    st.session_state["active_conversation_id"] = cid
    return cid


def rename_conversation(conversation_id: str, new_title: str):
    _ensure_state()
    if conversation_id in st.session_state["conversations"]:
        st.session_state["conversations"][conversation_id]["title"] = (new_title or "Sem título").strip()


def delete_conversation(conversation_id: str):
    _ensure_state()
    convs = st.session_state["conversations"]

    if conversation_id in convs:
        del convs[conversation_id]

    # Se apagou tudo, recria uma conversa
    if not convs:
        new_conversation("Novo chat")
        return

    # Se apagou a ativa, aponta pra primeira restante
    if st.session_state.get("active_conversation_id") == conversation_id:
        st.session_state["active_conversation_id"] = next(iter(convs.keys()))


def get_history(conversation_id: str | None = None):
    """
    Retorna lista de mensagens [{'role': 'user'|'assistant', 'content': str}, ...]
    """
    _ensure_state()
    cid = conversation_id or get_active_id()
    if cid not in st.session_state["conversations"]:
        return []
    return st.session_state["conversations"][cid].get("messages", [])


def add_message(role: str, content: str, conversation_id: str | None = None):
    _ensure_state()
    cid = conversation_id or get_active_id()
    if cid not in st.session_state["conversations"]:
        # fallback: cria e usa
        cid = new_conversation("Novo chat")

    st.session_state["conversations"][cid]["messages"].append(
        {"role": role, "content": content}
    )

