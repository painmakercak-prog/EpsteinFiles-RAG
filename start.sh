#!/usr/bin/env bash
set -euo pipefail

CHROMA_DB_DATASET="${CHROMA_DB_DATASET:-devankit7873/EpsteinFiles-Vector-Embeddings-ChromaDB}"

if [ ! -d "./chroma_db" ] || [ -z "$(ls -A ./chroma_db 2>/dev/null)" ]; then
    echo "📦 chroma_db not found locally — downloading precomputed embeddings from ${CHROMA_DB_DATASET}..."
    DOWNLOAD_DIR="$(mktemp -d)"
    huggingface-cli download "${CHROMA_DB_DATASET}" \
        --repo-type dataset \
        --local-dir "${DOWNLOAD_DIR}"
    mv "${DOWNLOAD_DIR}/chroma_db" ./chroma_db
    rm -rf "${DOWNLOAD_DIR}"
    echo "✅ chroma_db ready."
else
    echo "✅ chroma_db already present, skipping download."
fi

echo "🚀 Starting FastAPI backend on 127.0.0.1:8000..."
uvicorn api.main:app --host 127.0.0.1 --port 8000 &
API_PID=$!

cleanup() {
    kill "${API_PID}" 2>/dev/null || true
}
trap cleanup EXIT

echo "⏳ Waiting for API to become healthy..."
for _ in $(seq 1 60); do
    if curl -sf "http://127.0.0.1:8000/docs" >/dev/null 2>&1; then
        break
    fi
    sleep 1
done

echo "🚀 Starting Streamlit UI on 0.0.0.0:${PORT:-7860}..."
exec streamlit run app.py \
    --server.address=0.0.0.0 \
    --server.port="${PORT:-7860}" \
    --server.headless=true \
    --server.enableCORS=false \
    --server.enableXsrfProtection=false
