"""Streamlit interface for the Analytics Agent FastAPI service."""

from __future__ import annotations

import json
import os
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

import streamlit as st


API_URL = os.getenv("API_URL", "http://127.0.0.1:8000").rstrip("/")


class APIError(Exception):
    """Readable error returned when the FastAPI service cannot be reached."""


def api_request(path: str, *, method: str = "GET", payload: dict | None = None):
    body = json.dumps(payload).encode("utf-8") if payload is not None else None
    request = Request(
        f"{API_URL}{path}",
        data=body,
        headers={"Content-Type": "application/json"},
        method=method,
    )
    try:
        with urlopen(request, timeout=120) as response:
            return json.loads(response.read().decode("utf-8"))
    except HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise APIError(f"L’API a répondu avec le statut {exc.code} : {detail}") from exc
    except (URLError, TimeoutError) as exc:
        raise APIError(
            f"Impossible de joindre l’API à {API_URL}. Vérifiez qu’elle est démarrée."
        ) from exc
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise APIError("L’API a renvoyé une réponse illisible.") from exc


def create_session() -> dict:
    return api_request("/api/sessions", method="POST")


def load_messages(session_id: str) -> list[dict]:
    result = api_request(f"/api/sessions/{session_id}/messages")
    return result.get("messages", [])


st.set_page_config(page_title="Analytics Agent", page_icon="", layout="wide")
st.title("Analytics Agent")
st.caption("Posez vos questions sur les données e-commerce en langage naturel.")

if "sessions" not in st.session_state:
    st.session_state.sessions = {}
if "active_session_id" not in st.session_state:
    st.session_state.active_session_id = None
if "sql_history" not in st.session_state:
    st.session_state.sql_history = {}


def start_session() -> None:
    try:
        session = create_session()
    except APIError as exc:
        st.sidebar.error(str(exc))
        return
    session_id = str(session["id"])
    st.session_state.sessions[session_id] = session.get("title") or "Nouvelle conversation"
    st.session_state.active_session_id = session_id


with st.sidebar:
    st.subheader("Conversations")
    if st.button("＋ Nouvelle conversation", use_container_width=True):
        start_session()

    for session_id, title in reversed(list(st.session_state.sessions.items())):
        label = title
        if st.button(label, key=f"session_{session_id}", use_container_width=True):
            st.session_state.active_session_id = session_id

    st.divider()
    st.caption(f"API : `{API_URL}`")

if st.session_state.active_session_id is None:
    start_session()

session_id = st.session_state.active_session_id
if session_id is None:
    st.info("Démarrez l’API FastAPI, puis rechargez cette page.")
    st.stop()

try:
    messages = load_messages(session_id)
except APIError as exc:
    st.error(str(exc))
    st.stop()

for index, message in enumerate(messages):
    role = message.get("role", "assistant")
    with st.chat_message("user" if role == "user" else "assistant"):
        st.markdown(message.get("content", ""))
        if role == "assistant":
            history = st.session_state.sql_history.get(session_id, {})
            for sql_item in history.get(index, []):
                with st.expander("Voir la requête SQL et son résultat"):
                    st.code(sql_item.get("query", ""), language="sql")
                    st.text(sql_item.get("result", ""))

question = st.chat_input("Ex. Quelle catégorie a généré le plus de ventes ?")
if question:
    with st.chat_message("user"):
        st.markdown(question)
    with st.chat_message("assistant"):
        with st.spinner("Analyse en cours…"):
            try:
                response = api_request(
                    f"/api/sessions/{session_id}/messages",
                    method="POST",
                    payload={"message": question},
                )
                st.markdown(response.get("answer", "Aucune réponse reçue."))
                sql_history = response.get("sql_history", [])
                if sql_history:
                    with st.expander("Voir les requêtes SQL et leurs résultats"):
                        for sql_item in sql_history:
                            st.code(sql_item.get("query", ""), language="sql")
                            st.text(sql_item.get("result", ""))

                # API history alternates user/assistant messages; the new answer
                # is therefore at the final even index after the POST succeeds.
                answer_index = len(messages) + 1
                st.session_state.sql_history.setdefault(session_id, {})[answer_index] = sql_history
            except APIError as exc:
                st.error(str(exc))
