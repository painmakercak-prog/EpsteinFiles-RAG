from pathlib import Path

import numpy as np
from fastapi.testclient import TestClient

from api import main


def test_vector_database_ready_requires_real_files(tmp_path: Path) -> None:
    assert not main.vector_database_ready(tmp_path)

    sqlite = tmp_path / "chroma.sqlite3"
    index = tmp_path / "collection" / "data_level0.bin"
    index.parent.mkdir()
    sqlite.write_bytes(b"0" * 1_000_001)
    index.write_bytes(b"0" * 1_000_001)

    assert main.vector_database_ready(tmp_path)


def test_mmr_can_prefer_relevance_then_diversity() -> None:
    query = np.array([1.0, 0.0], dtype=np.float32)
    candidates = np.array(
        [
            [1.0, 0.0],
            [0.999, 0.01],
            [0.8, 0.6],
        ],
        dtype=np.float32,
    )

    assert main.mmr_indices(query, candidates, k=2, lambda_mult=0.45) == [0, 2]


def test_ask_returns_grounded_answer_and_unique_sources(monkeypatch) -> None:
    documents = [
        main.RetrievedDocument("First excerpt", "file-a.txt", 0.9),
        main.RetrievedDocument("Second excerpt", "file-a.txt", 0.8),
        main.RetrievedDocument("Third excerpt", "file-b.txt", 0.7),
    ]
    monkeypatch.setattr(main, "retrieve", lambda _question: documents)
    monkeypatch.setattr(main, "generate_answer", lambda _question, _documents: "Grounded answer")

    response = TestClient(main.app).post("/ask", params={"question": "What happened?"})

    assert response.status_code == 200
    assert response.json() == {
        "answer": "Grounded answer",
        "sources": ["file-a.txt", "file-b.txt"],
    }
