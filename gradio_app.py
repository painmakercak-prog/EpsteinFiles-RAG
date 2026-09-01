"""Gradio entrypoint, used by the Hugging Face Space.

Spaces offers Gradio, Docker, and Static SDKs; Docker is a paid feature, so the
free deployment runs here rather than through `app.py` (Streamlit) or the
FastAPI service in `api/main.py`. Retrieval and answering are imported from
`api.main` so all three entrypoints share one implementation.
"""

import gradio as gr

from api.main import generate_answer, retrieve
from bootstrap import ensure_vector_database

DESCRIPTION = "Single-query factual answers grounded in the document archive."

EXAMPLES = [
    "Which banks are mentioned in the documents?",
    "What flight records appear in the files?",
    "Which properties are referenced?",
]


def answer_question(question: str) -> tuple[str, str]:
    question = (question or "").strip()
    if len(question) < 2:
        return "Enter a question first.", ""

    try:
        documents = retrieve(question)
    except RuntimeError as error:
        return f"The archive is not available: {error}", ""

    if not documents:
        return "I could not find this information in the retrieved documents.", ""

    try:
        answer = generate_answer(question, documents)
    except RuntimeError as error:
        return f"Could not generate an answer: {error}", ""

    sources = list(dict.fromkeys(document.source for document in documents))
    return answer, "**Sources:** " + ", ".join(sources)


with gr.Blocks(title="Epstein Files RAG", theme=gr.themes.Soft()) as demo:
    gr.Markdown(f"# 📄 Epstein Files RAG\n{DESCRIPTION}")

    question_box = gr.Textbox(
        label="Question",
        placeholder="Ask a factual question (e.g. Which banks are mentioned?)",
        lines=2,
    )
    search_button = gr.Button("Search Documents", variant="primary")

    answer_box = gr.Markdown(label="Answer")
    sources_box = gr.Markdown()

    gr.Examples(examples=EXAMPLES, inputs=question_box)

    search_button.click(
        answer_question,
        inputs=question_box,
        outputs=[answer_box, sources_box],
    )
    question_box.submit(
        answer_question,
        inputs=question_box,
        outputs=[answer_box, sources_box],
    )

if __name__ == "__main__":
    # Download and validate the precomputed vector store before serving, so the
    # Space only accepts traffic once searches can actually be answered.
    ensure_vector_database()
    demo.queue().launch()
