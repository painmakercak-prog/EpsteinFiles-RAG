import os
from pathlib import Path

VECTOR_DATASET_REPO = os.getenv(
    "VECTOR_DATASET_REPO",
    "devankit7873/EpsteinFiles-Vector-Embeddings-ChromaDB",
)
CHROMA_COLLECTION = os.getenv("CHROMA_COLLECTION", "epstein")


def vector_database_ready(directory: Path) -> bool:
    sqlite = directory / "chroma.sqlite3"
    indexes = list(directory.glob("*/data_level0.bin"))
    return (
        sqlite.is_file()
        and sqlite.stat().st_size > 1_000_000
        and any(index.stat().st_size > 1_000_000 for index in indexes)
    )


def validate_vector_database(directory: Path) -> int:
    import chromadb

    client = chromadb.PersistentClient(path=str(directory))
    available = [
        getattr(collection, "name", str(collection))
        for collection in client.list_collections()
    ]
    collection_name = CHROMA_COLLECTION
    if collection_name not in available:
        if len(available) == 1:
            collection_name = available[0]
        else:
            raise RuntimeError(
                f"Collection {CHROMA_COLLECTION!r} not found; available collections: {available}"
            )

    count = client.get_collection(collection_name).count()
    if count < 1:
        raise RuntimeError(f"Vector collection {collection_name!r} is empty")
    return count


def ensure_vector_database() -> Path:
    target = Path(os.getenv("CHROMA_DIR", "./chroma_db")).resolve()
    if vector_database_ready(target):
        count = validate_vector_database(target)
        print(f"Vector database ready at {target} ({count:,} records)", flush=True)
        return target

    if os.getenv("SKIP_VECTOR_BOOTSTRAP") == "1":
        print("Skipping vector database download", flush=True)
        return target

    expected_download_path = target.parent / "chroma_db"
    if target != expected_download_path:
        raise RuntimeError("CHROMA_DIR must end with /chroma_db when automatic download is enabled")

    target.parent.mkdir(parents=True, exist_ok=True)
    print(f"Downloading precomputed vector database from {VECTOR_DATASET_REPO}", flush=True)

    from huggingface_hub import snapshot_download

    snapshot_download(
        repo_id=VECTOR_DATASET_REPO,
        repo_type="dataset",
        allow_patterns=["chroma_db/**"],
        local_dir=str(target.parent),
    )

    if not vector_database_ready(target):
        raise RuntimeError(f"Vector database download did not produce a valid index at {target}")

    count = validate_vector_database(target)
    print(f"Vector database downloaded to {target} ({count:,} records)", flush=True)
    return target


if __name__ == "__main__":
    ensure_vector_database()
