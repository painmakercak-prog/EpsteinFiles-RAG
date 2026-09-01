import html
import os

import requests
import streamlit as st

# -----------------------------
# Page config
# -----------------------------
st.set_page_config(
    page_title="Epstein Files RAG",
    page_icon="📄",
    layout="centered"
)

# -----------------------------
# Modern CSS
# -----------------------------
st.markdown("""
<style>
html, body, [class*="css"] {
    font-family: Inter, system-ui, sans-serif;
    background: radial-gradient(circle at top, #111827, #030712 65%);
    color: #e5e7eb;
}

.block-container {
    max-width: 760px;
    padding-top: 2.5rem;
}

.title {
    text-align: center;
    font-size: 2.4rem;
    font-weight: 700;
    background: linear-gradient(90deg, #60a5fa, #a78bfa);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
}

.subtitle {
    text-align: center;
    color: #9ca3af;
    font-size: 0.95rem;
    margin-bottom: 2rem;
}

/* Input */
.stTextInput input {
    border-radius: 14px;
    background: rgba(31, 41, 55, 0.85);
    border: 1px solid rgba(255,255,255,0.08);
    padding: 0.7rem;
}

/* Button */
.stButton>button {
    width: 100%;
    border-radius: 14px;
    font-weight: 500;
    padding: 0.65rem;
    background: linear-gradient(90deg, #2563eb, #7c3aed);
    border: none;
}

/* Q&A cards */
.chat {
    background: rgba(31, 41, 55, 0.75);
    backdrop-filter: blur(10px);
    border-radius: 14px;
    padding: 1rem 1.1rem;
    margin-top: 1.2rem;
    border: 1px solid rgba(255,255,255,0.04);
}

.user {
    box-shadow: inset 3px 0 0 #22c55e;
}

.assistant {
    box-shadow: inset 3px 0 0 #3b82f6;
}

.role {
    font-size: 0.75rem;
    color: #9ca3af;
    margin-bottom: 0.25rem;
}

/* Footer */
.footer {
    text-align: center;
    color: #6b7280;
    font-size: 0.8rem;
    margin-top: 3rem;
}
</style>
""", unsafe_allow_html=True)

# -----------------------------
# Header
# -----------------------------
st.markdown("<div class='title'>📄 Epstein Files RAG</div>", unsafe_allow_html=True)
st.markdown(
    "<div class='subtitle'>Single-query factual answers grounded in the document archive</div>",
    unsafe_allow_html=True
)

# -----------------------------
# API
# -----------------------------
API_URL = os.getenv("API_URL", "http://127.0.0.1:8000/ask")

# -----------------------------
# Session state (single-shot)
# -----------------------------
if "qa" not in st.session_state:
    st.session_state.qa = None

if "input_key" not in st.session_state:
    st.session_state.input_key = 0  # forces input reset

# -----------------------------
# Input
# -----------------------------
question = st.text_input(
    label="Question",
    placeholder="Ask a factual question (e.g. Which banks are mentioned?)",
    label_visibility="collapsed",
    key=f"question_{st.session_state.input_key}"
)

ask_button = st.button("Search Documents")

# -----------------------------
# Handle question
# -----------------------------
if ask_button and question.strip():
    # remove previous Q&A
    st.session_state.qa = None

    with st.spinner("Analyzing documents…"):
        try:
            response = requests.post(
                API_URL,
                params={"question": question},
                timeout=120
            )

            if response.status_code == 200:
                payload = response.json()
                answer = payload.get("answer", "")
                sources = payload.get("sources", [])
            else:
                answer = "⚠️ Server error."
                sources = []

        except Exception as e:
            answer = f"⚠️ API connection failed: {e}"
            sources = []

    # store current Q&A only
    st.session_state.qa = (question, answer, sources)

    # clear input box
    st.session_state.input_key += 1
    st.rerun()

# -----------------------------
# Display single Q&A
# -----------------------------
if st.session_state.qa:
    q, a, sources = st.session_state.qa
    safe_question = html.escape(q)
    safe_answer = html.escape(a).replace("\n", "<br>")

    st.markdown(
        f"""
        <div class='chat user'>
            <div class='role'>Question</div>
            {safe_question}
        </div>
        """,
        unsafe_allow_html=True
    )

    st.markdown(
        f"""
        <div class='chat assistant'>
            <div class='role'>Answer</div>
            {safe_answer}
        </div>
        """,
        unsafe_allow_html=True
    )

    if sources:
        st.caption("Sources: " + ", ".join(str(source) for source in sources))

# -----------------------------
# Footer
# -----------------------------
st.markdown(
    """
    <div class='footer'>
        Made by 
        <a href="https://github.com/AnkitNayak-eth" target="_blank"
           style="color:#60a5fa; text-decoration:none; font-weight:600;">
            Ankit ❤️
        </a>
    </div>
    """,
    unsafe_allow_html=True
)

st.caption(
    "Research tool: a name appearing in a record does not by itself establish misconduct. "
    "Verify important claims against the cited source document."
)
