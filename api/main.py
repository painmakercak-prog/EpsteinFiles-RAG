import os
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Any

import numpy as np
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import JSONResponse

load_dotenv()

app = FastAPI(title="Epstein Files RAG", version="1.0.0")

CHROMA_DIR = Path(os.getenv("CHROMA_DIR", "./chroma_db"))
CHROMA_COLLECTION = os.getenv("CHROMA_COLLECTION", "epstein")
GROQ_MODEL = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")
FETCH_K = int(os.getenv("RETRIEVAL_FETCH_K", "60"))
RESULT_K = int(os.getenv("RETRIEVAL_RESULT_K", "12"))


@dataclass(frozen=True)
class RetrievedDocument:
    text: str
    source: str
    score: float


def vector_database_ready(directory: Path = CHROMA_DIR) -> bool:
    sqlite = directory / "chroma.sqlite3"
    indexes = list(directory.glob("*/data_level0.bin"))
    return (
        sqlite.is_file()
        and sqlite.stat().st_size > 1_000_000
        and any(index.stat().st_size > 1_000_000 for index in indexes)
    )


def mmr_indices(
    query: np.ndarray,
    candidates: np.ndarray,
    k: int,
    lambda_mult: float = 0.65,
) -> list[int]:
    if candidates.ndim != 2 or not len(candidates) or k <= 0:
        return []

    query_norm = np.linalg.norm(query)
    candidate_norms = np.linalg.norm(candidates, axis=1, keepdims=True)
    normalized_query = query / query_norm if query_norm else query
    normalized = candidates / np.where(candidate_norms == 0, 1, candidate_norms)
    relevance = normalized @ normalized_query

    selected: list[int] = []
    remaining = set(range(len(candidates)))

    while remaining and len(selected) < min(k, len(candidates)):
        if not selected:
            choice = max(remaining, key=lambda index: float(relevance[index]))
        else:
            choice = max(
                remaining,
                key=lambda index: (
                    lambda_mult * float(relevance[index])
                    - (1 - lambda_mult)
                    * max(float(normalized[index] @ normalized[picked]) for picked in selected)
                ),
            )
        selected.append(choice)
        remaining.remove(choice)

    return selected


@lru_cache(maxsize=1)
def get_vector_store() -> tuple[Any, Any]:
    if not vector_database_ready():
        raise RuntimeError(f"Vector database is missing from {CHROMA_DIR}")

    import chromadb
    from chromadb.utils.embedding_functions import DefaultEmbeddingFunction

    client = chromadb.PersistentClient(path=str(CHROMA_DIR))
    available = [getattr(collection, "name", str(collection)) for collection in client.list_collections()]
    collection_name = CHROMA_COLLECTION
    if collection_name not in available:
        if len(available) == 1:
            collection_name = available[0]
        else:
            raise RuntimeError(
                f"Collection {CHROMA_COLLECTION!r} not found; available collections: {available}"
            )

    embedding_function = DefaultEmbeddingFunction()
    collection = client.get_collection(
        name=collection_name,
        embedding_function=embedding_function,
    )
    return collection, embedding_function


def retrieve(question: str) -> list[RetrievedDocument]:
    collection, embedding_function = get_vector_store()
    count = collection.count()
    if count == 0:
        return []

    query_embedding = np.asarray(embedding_function([question])[0], dtype=np.float32)
    results = collection.query(
        query_embeddings=[query_embedding.tolist()],
        n_results=min(FETCH_K, count),
        include=["documents", "metadatas", "embeddings"],
    )

    documents_batch = results.get("documents")
    documents = documents_batch[0] if documents_batch else []
    if not documents:
        return []

    metadata_batch = results.get("metadatas")
    metadata = metadata_batch[0] if metadata_batch else [{} for _ in documents]
    embeddings_batch = results.get("embeddings")
    vectors = np.asarray(embeddings_batch[0], dtype=np.float32) if embeddings_batch is not None else None

    if vectors is not None and vectors.ndim == 2 and len(vectors) == len(documents):
        selected = mmr_indices(query_embedding, vectors, RESULT_K)
        normalized_query = query_embedding / max(float(np.linalg.norm(query_embedding)), 1e-12)
        normalized_vectors = vectors / np.maximum(np.linalg.norm(vectors, axis=1, keepdims=True), 1e-12)
        scores = normalized_vectors @ normalized_query
    else:
        selected = list(range(min(RESULT_K, len(documents))))
        scores = np.zeros(len(documents), dtype=np.float32)

    retrieved: list[RetrievedDocument] = []
    for index in selected:
        details = metadata[index] or {}
        retrieved.append(
            RetrievedDocument(
                text=str(documents[index]),
                source=str(details.get("source") or details.get("file") or "unknown document"),
                score=float(scores[index]),
            )
        )
    return retrieved


def generate_answer(question: str, documents: list[RetrievedDocument]) -> str:
    api_key = os.getenv("GROQ_API_KEY", "").strip()
    if not api_key:
        raise RuntimeError("GROQ_API_KEY is not configured")

    from groq import Groq

    context = "\n\n".join(
        f"[Source: {document.source}]\n{document.text}" for document in documents
    )
    client = Groq(api_key=api_key)
    response = client.chat.completions.create(
        model=GROQ_MODEL,
        temperature=0,
        max_tokens=650,
        messages=[
            {
                "role": "system",
                "content": (
                    "Answer only from the supplied document excerpts. Distinguish a mere mention, "
                    "an allegation, testimony, and an established fact; never imply wrongdoing from a "
                    "name appearing in the records alone. If the excerpts do not answer the question, "
                    "say you could not find it in the retrieved documents. Be concise and cite source "
                    "filenames in brackets."
                ),
            },
            {
                "role": "user",
                "content": f"Context:\n{context}\n\nQuestion:\n{question}",
            },
        ],
    )
    return (response.choices[0].message.content or "").strip()


@app.get("/healthz")
def healthz() -> dict[str, object]:
    return {
        "ok": True,
        "vectorDatabase": vector_database_ready(),
        "groqConfigured": bool(os.getenv("GROQ_API_KEY", "").strip()),
        "model": GROQ_MODEL,
    }


@app.get("/readyz")
def readyz() -> JSONResponse:
    ready = vector_database_ready() and bool(os.getenv("GROQ_API_KEY", "").strip())
    return JSONResponse({"ready": ready}, status_code=200 if ready else 503)


@app.post("/ask")
def ask(question: str = Query(min_length=2, max_length=1000)) -> dict[str, object]:
    try:
        documents = retrieve(question.strip())
        if not documents:
            return {
                "answer": "I could not find this information in the retrieved documents.",
                "sources": [],
            }

        answer = generate_answer(question.strip(), documents)
        sources = list(dict.fromkeys(document.source for document in documents))
        return {"answer": answer, "sources": sources}
    except RuntimeError as error:
        raise HTTPException(status_code=503, detail=str(error)) from error
