# Deploying to Hugging Face Spaces

Spaces offers Gradio, Docker, and Static SDKs. Docker is a paid feature and
Static cannot run Python, so the free deployment uses the **Gradio SDK** on
**CPU basic** hardware (16GB RAM).

`gradio_app.py` is the Space entrypoint. It imports `retrieve()` and
`generate_answer()` from `api/main.py`, so the Gradio UI, the Streamlit UI
(`app.py`), and the FastAPI service all share one implementation. Before
serving, it runs `bootstrap.ensure_vector_database()` to download the
precomputed vector store from
[`devankit7873/EpsteinFiles-Vector-Embeddings-ChromaDB`](https://huggingface.co/datasets/devankit7873/EpsteinFiles-Vector-Embeddings-ChromaDB),
so the Space only accepts traffic once searches can be answered.

## 1. Create the Space

https://huggingface.co/new-space

- Name: `epsteinfiles-rag`
- SDK: **Gradio**, template **Blank**
- Hardware: **CPU basic** (free)

## 2. Add your Groq API key

Space → **Settings → Variables and secrets** → new secret:

- `GROQ_API_KEY` = your key from https://console.groq.com

## 3. Get the code into the Space

### Option A — automatic, via GitHub Actions

`.github/workflows/sync-space.yml` pushes `main` to the Space on every commit.
It needs one GitHub repository secret:

- GitHub repo → **Settings → Secrets and variables → Actions**
- New repository secret: `HF_TOKEN` = a Hugging Face token with **write** access
  (https://huggingface.co/settings/tokens)

If the Space is not named `kacarroll89/epsteinfiles-rag`, also add a repository
**variable** `HF_SPACE` set to `<owner>/<space-name>`.

Then run the workflow from the **Actions** tab, or push any commit to `main`.

### Option B — manual, from a terminal

```bash
git remote add space https://<hf-username>:<hf-write-token>@huggingface.co/spaces/<hf-username>/epsteinfiles-rag
git push space main:main --force
```

`README.md` already carries the Space YAML header (`sdk: gradio`,
`app_file: gradio_app.py`), so the Space configures itself from the push.

## 4. First start

The first boot downloads ~1.1GB of embeddings before the UI comes up, so expect
several minutes on the initial build. Searches are fast once it is running.
Spaces storage is ephemeral: a restarted Space downloads the index again on the
next start unless persistent storage is enabled.

## Notes

- `requirements.txt` installs runtime dependencies plus Gradio. The heavier
  ingest stack (`sentence-transformers`, `datasets`, LangChain) lives in
  `requirements-ingest.txt` and is only needed to rebuild the vector store from
  scratch with the `ingest/` scripts.
- The app needs real memory — 100K+ chunks over a ~1.1GB index. Free tiers with
  ~512MB (such as Railway's trial) OOM-kill the process mid-search, which
  surfaces in the UI as a dropped connection. Spaces' free CPU basic tier has
  16GB.
- `Dockerfile` / `start.py` still exist for Docker hosts, where `start.py` sets
  `API_URL` and runs FastAPI alongside Streamlit.
