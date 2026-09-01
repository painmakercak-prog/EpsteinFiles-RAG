# EpsteinFiles-RAG
A RAG pipeline implementation built on the 'Epstein Files 20K' dataset from Hugging Face (Teyler).

![Recording 2026-02-10 230408](https://github.com/user-attachments/assets/e7378680-b113-442e-b112-7745197ade65)

## Dataset source
👉 https://huggingface.co/datasets/teyler/epstein-files-20k

## Precomputed Embeddings
👉 https://huggingface.co/datasets/devankit7873/EpsteinFiles-Vector-Embeddings-ChromaDB


---

## ⚡ Quick Demo

Process 2M+ document lines → Get accurate, grounded answers in seconds

**What it does:**
- Automatically cleans and reconstructs fragmented documents
- Intelligently chunks documents while preserving context
- Embeds everything into a searchable vector database
- Retrieves diverse, relevant information using MMR algorithm
- Generates answers grounded solely in the retrieved context

---

## 🎯 Key Features

✅ **No Hallucinations** - Answers only from source documents  
✅ **Intelligent Retrieval** - MMR algorithm for diverse results  
✅ **Fast Processing** - ~1 second end-to-end query response  
✅ **Semantic Understanding** - Context-aware document chunking  
✅ **REST API** - Easy integration with other systems  
✅ **Interactive UI** - Streamlit web interface included  
✅ **Scalable** - Handles 100K+ document chunks  
✅ **Production-Ready** - Async support, error handling, logging  

---

## 🏗️ How It Works

### Three Simple Stages

**Stage 1: Data Preparation**
```
Raw Documents (2.5M lines)
    ↓
Clean & Reconstruct
    ↓
Smart Chunking
    ↓
Vector Embeddings
```

**Stage 2: Intelligent Retrieval**
```
User Question
    ↓
Find Similar Context (MMR)
    ↓
Return Top Chunks
```

**Stage 3: Grounded Answer**
```
Context + Question
    ↓
LLaMA 3.3 LLM
    ↓
Grounded Answer (with sources)
```

### Why MMR Instead of Similarity?

**Previous Approach:** Pure semantic similarity  
→ Returned redundant chunks from same document

**Current Approach:** Maximal Marginal Relevance (MMR)  
→ Balances relevance + diversity for comprehensive context

---

## 📦 Installation

### Requirements
- Python 3.11+
- 16GB RAM (8GB minimum)
- Groq API key (free at [console.groq.com](https://console.groq.com))

### Setup (5 minutes)

**1. Clone repository**
```bash
git clone https://github.com/AnkitNayak-eth/EpsteinFiles-RAG.git
cd EpsteinFiles-RAG
```

**2. Create virtual environment**
```bash
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
```

**3. Install dependencies**
```bash
pip install -r requirements.txt
```

**4. Configure environment**

Create `.env` file:
```
GROQ_API_KEY=your_api_key_here
```

## 🚀 Getting Started

### Run Complete Pipeline (First Time)

This processes data and prepares the system for queries:

```bash
# Stage 1: Download raw data (~5-15 min)
python ingest/download_dataset.py

# Stage 2: Clean and reconstruct documents (~3-8 min)
python ingest/clean_dataset.py

# Stage 3: Create semantic chunks (~5-12 min)
python ingest/chunk_dataset.py

# Stage 4: Generate embeddings (~20-45 min)
python ingest/embed_chunks.py
```

### Start Using the System

**Terminal 1 - Start API Server**
```bash
uvicorn api.main:app --reload
```
API runs at: `http://127.0.0.1:8000`

**Terminal 2 - Start Web UI**
```bash
streamlit run app.py
```
UI opens at: `http://localhost:8501`

**That's it!** You can now query through the web interface or API.

### Deploy on Railway

The repository includes a production Docker image, Railway configuration, a process supervisor for FastAPI + Streamlit, and a GitHub Actions CI/deploy workflow.

1. Create a Railway service from this GitHub repository.
2. Add `GROQ_API_KEY` to the service variables.
3. Deploy. The Docker build downloads the precomputed Chroma database from Hugging Face, so the first build is large but does not repeat the embedding pipeline.
4. Generate a public domain in Railway's Networking settings.

Railway serves Streamlit on its injected `PORT`; FastAPI remains private on `127.0.0.1:8000`. The health-check path is `/_stcore/health`. If you use a Railway deploy hook instead of its GitHub integration, save the hook as the GitHub Actions secret `RAILWAY_DEPLOY_HOOK`.

---
## 📚 Project Structure

```
EpsteinFiles-RAG/
├── ingest/                    # Data processing pipeline
│   ├── download_dataset.py    # Download from Hugging Face
│   ├── clean_dataset.py       # Clean & reconstruct docs
│   ├── chunk_dataset.py       # Semantic chunking
│   └── embed_chunks.py        # Embed & index
├── api/                       # FastAPI backend
│   ├── main.py               # API routes
│   └── models.py             # Data models
├── app.py                     # Streamlit UI
├── requirements.txt           # Python dependencies
├── .env.example              # Environment template
└── README.md                 # This file
```

---

## 📜 License

This project is licensed under the **MIT License** - see the [LICENSE](LICENSE) file for details.

---

## 🙏 Acknowledgments

- **Dataset:** [Teyler/Epstein Files 20K](https://huggingface.co/datasets/teyler/epstein-files-20k) on Hugging Face
- **Embeddings:** [Sentence Transformers](https://www.sbert.net/)
- **Vector DB:** [Chroma](https://www.trychroma.com/)
- **LLM Inference:** [Groq Cloud](https://console.groq.com/)
- **Framework:** [LangChain](https://www.langchain.com/)
- **UI:** [Streamlit](https://streamlit.io/)

---

## 📞 Support

**Built by:** Ankit Kumar Nayak  
**Full-Stack Developer | AI & RAG Systems**

**Get Help:**
- 📝 [Open an Issue](https://github.com/AnkitNayak-eth/EpsteinFiles-RAG/issues)
- 💬 [Start a Discussion](https://github.com/AnkitNayak-eth/EpsteinFiles-RAG/discussions)

---

## ⚠️ Disclaimer

This project is built for **research, transparency, and educational purposes**. All data is sourced from public records. Users are responsible for complying with applicable laws and ethical guidelines when using this system.

---
