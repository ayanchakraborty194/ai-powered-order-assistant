"""Streamlit chat UI for the Order Processing Data Assistant PoC.

Talks to the FastAPI backend's /query endpoint. Run with:
    streamlit run streamlit_app/app.py
"""

import os
import uuid

import requests
import streamlit as st

BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000/api/v1")
QUERY_ENDPOINT = f"{BACKEND_URL}/query"

st.set_page_config(page_title="Order Processing Data Assistant", page_icon="📦", layout="centered")

st.title("📦 Order Processing Data Assistant")
st.caption(
    "Ask questions about orders, customers, products, and shipments in plain English."
)

if "thread_id" not in st.session_state:
    st.session_state.thread_id = str(uuid.uuid4())

if "messages" not in st.session_state:
    st.session_state.messages = []

with st.sidebar:
    st.subheader("Session")
    st.text(f"Thread ID: {st.session_state.thread_id[:8]}...")
    if st.button("Start new conversation"):
        st.session_state.thread_id = str(uuid.uuid4())
        st.session_state.messages = []
        st.rerun()

    st.subheader("Example questions")
    examples = [
        "Show all orders for customer John Smith.",
        "What is the status of Order #100234?",
        "Which products were ordered in Order #10453?",
        "List pending shipments.",
        "Which customers have orders above $5,000?",
        "Show all delayed shipments.",
    ]
    for example in examples:
        if st.button(example, key=example):
            st.session_state.messages.append({"role": "user", "content": example})
            st.session_state.pending_query = example
            st.rerun()

# Render chat history
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])
        sql = message.get("sql")
        if sql:
            with st.expander("View SQL"):
                st.code(sql, language="sql")


def send_query(query_text: str) -> None:
    """Send a query to the backend and render the assistant's response.

    Args:
        query_text: The user's natural language question.
    """
    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            try:
                response = requests.post(
                    QUERY_ENDPOINT,
                    json={"thread_id": st.session_state.thread_id, "query": query_text},
                    timeout=45,
                )
                response.raise_for_status()
                data = response.json()
            except requests.RequestException as exc:
                st.error(f"Could not reach the assistant backend: {exc}")
                return

            answer = data.get("answer", "Sorry, something went wrong.")
            sql = data.get("sql")
            source = data.get("source")

            st.markdown(answer)
            if sql:
                with st.expander("View SQL"):
                    st.code(sql, language="sql")
                    if source:
                        st.caption(f"Resolved via: {source}")

            st.session_state.messages.append(
                {"role": "assistant", "content": answer, "sql": sql}
            )


# Handle example-button clicks queued from the sidebar
if st.session_state.get("pending_query"):
    pending = st.session_state.pop("pending_query")
    send_query(pending)

user_input = st.chat_input("Ask about orders, shipments, customers, or products...")
if user_input:
    st.session_state.messages.append({"role": "user", "content": user_input})
    with st.chat_message("user"):
        st.markdown(user_input)
    send_query(user_input)
