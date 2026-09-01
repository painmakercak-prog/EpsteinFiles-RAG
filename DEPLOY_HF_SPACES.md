# Deploying to Hugging Face Spaces

This repo runs on a **free Streamlit-SDK Space** (CPU basic — 16GB RAM, no
Docker required, since the Docker SDK is a paid Spaces feature).

On a Streamlit Space there is no separate API process: `app.py` detects that
`API_URL` is unset and calls the retrieval and answering code from
`api/main.py` directly in-process. On first search it downloads the
precomputed vector store from
[`devankit7873/EpsteinFiles-Vector-Embeddings-ChromaDB`](https://huggingface.co/datasets/devankit7873/EpsteinFiles-Vector-Embeddings-ChromaDB)
via `bootstrap.py`, then caches it for the life of the container.

The `Dockerfile`/`start.py` path still exists for Docker hosts (Railway, a
local container) — there `start.py` sets `API_URL` and runs FastAPI alongside
Streamlit, exactly as before.

## 1. Create the Space

- Go to https://huggingface.co/new-space
- Name it (e.g. `epsteinfiles-rag`), **SDK: Streamlit**, **Hardware: CPU basic (free)**

## 2. Add your Groq API key

Space → **Settings → Variables and secrets** → new secret:

- `GROQ_API_KEY` = your key from https://console.groq.com

## 3. Push this repo

```bash
git remote add space https://<hf-username>:<hf-write-token>@huggingface.co/spaces/<hf-username>/epsteinfiles-rag
git push space main:main --force
```

`README.md` already carries the Space YAML header (`sdk: streamlit`,
`app_file: app.py`), so the Space picks up its configuration from this push
with nothing to edit afterwards.

## 4. First search

The Space builds in a couple of minutes, but the **first search** is slow: it
downloads ~1.1GB of precomputed embeddings and loads the index. Later searches
in the same container are fast. Spaces storage is ephemeral, so a restarted
Space downloads it again on the next search — enable persistent storage if you
want to avoid that.

## Notes

- `requirements.txt` installs runtime dependencies only. The heavier ingest
  stack (`sentence-transformers`, `datasets`, LangChain) lives in
  `requirements-ingest.txt` and is only needed to rebuild the vector store from
  scratch with the `ingest/` scripts.
- The app needs real memory — the archive is 100K+ chunks over a ~1.1GB index.
  Free tiers with ~512MB (e.g. Railway's trial) will OOM-kill the process
  mid-search; Spaces' free CPU basic tier has 16GB.
