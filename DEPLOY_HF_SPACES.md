# Deploying to Hugging Face Spaces

This repo is set up to run as a single **Docker SDK** Space: the container
downloads and validates the precomputed vector store from
[`devankit7873/EpsteinFiles-Vector-Embeddings-ChromaDB`](https://huggingface.co/datasets/devankit7873/EpsteinFiles-Vector-Embeddings-ChromaDB)
during the image build, then starts FastAPI on `127.0.0.1:8000` and serves the
Streamlit UI (`app.py`) on the Space's public port. See `Dockerfile`,
`bootstrap.py`, and `start.py` for the details.

I don't have Hugging Face write/push access from this session (only
read-only Hub tools), so the last step — creating the Space and pushing —
needs to be done from your own account:

## 1. Create the Space

- Go to https://huggingface.co/new-space
- Pick an owner/name, set **SDK** to **Docker**, visibility as you like.
- Don't initialize it with a README — you'll push this repo's contents.

## 2. Add the Space README metadata

Hugging Face Spaces require a YAML header at the top of the Space's
`README.md` (this repo's own `README.md` is left untouched so GitHub
rendering isn't affected — add this header only in the Space's copy):

```yaml
---
title: EpsteinFiles RAG
emoji: 📄
colorFrom: blue
colorTo: purple
sdk: docker
app_port: 7860
pinned: false
license: mit
---
```

Prepend that to the top of `README.md` before pushing, or add it directly
in the Space's web UI after the first push.

## 3. Add your Groq API key as a Space secret

In the Space's **Settings → Variables and secrets**, add:

- `GROQ_API_KEY` = your key from https://console.groq.com

## 4. Push this repo to the Space

Spaces are their own git remote:

```bash
git remote add space https://huggingface.co/spaces/<your-username>/<space-name>
git push space claude/github-repo-deploy-g0j4hh:main
```

(Use `huggingface-cli login` first, or an access token with write scope, if
you haven't authenticated git to the Hub before.)

## 5. First boot

The first build will take a while: the container downloads and validates the
~1.1GB precomputed Chroma DB from the Hugging Face dataset. The completed index
is baked into the image, so ordinary container restarts do not re-download it.

## Notes / things you may want to change

- `ingest/` scripts are for regenerating the dataset from scratch and are
  not used at deploy time — deployment relies on the precomputed embeddings
  dataset instead, since embedding 100K+ chunks from a cold start would make
  the Space take ~30–60 min to become usable.
- The FastAPI backend isn't exposed outside the container — only the
  Streamlit UI is reachable at the Space's public URL, which talks to the
  API over localhost inside the same container.
