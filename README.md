# Agentic RAG

A web app for natural language question answering over personal documents using agentic retrieval.

## Architecture

**Hybrid Retrieval:**
- **Vector search** (ChromaDB + OpenAI embeddings): Semantic similarity for conceptual queries
- **Keyword search** (BM25): Literal word matching for specific terms/names

The LangChain ReAct agent decides which tools to use based on the question:
- Uses both tools for most queries
- Synthesizes results with citations

## Supported Formats

- `.md` (Markdown)
- `.txt` (Plain text)

## Project Structure

```
.
├── backend/
│   ├── api/
│   │   └── main.py          # FastAPI server
│   ├── agents/
│   │   ├── query_agent.py   # ReAct agent
│   │   └── tools/           # Vector and keyword search tools
│   ├── utils/
│   │   ├── chroma_store.py  # ChromaDB wrapper
│   │   ├── document_loader.py
│   │   └── keyword_search.py # BM25 implementation
│   ├── chroma_data/         # Persistent ChromaDB storage
│   └── .env.example
├── frontend/
│   └── app/                 # Next.js app
│       ├── components/
│       │   ├── Chat.tsx
│       │   └── FileDrop.tsx
│       ├── layout.tsx
│       └── page.tsx
├── requirements.txt
└── README.md
```

## Setup

### Backend (Python)

```bash
# Create conda environment
conda create -n agentic-rag python=3.11
conda activate agentic-rag

# Install dependencies
pip install -r requirements.txt

#add .env to backend folder

# Start server
cd backend
python -m api.main
```

### Frontend (Next.js)

```bash
cd frontend
npm install
npm run dev
```

Open http://localhost:3000

## Usage

1. Drop `.md` or `.txt` files in the sidebar
2. Files are chunked and indexed on upload
3. Ask questions in the chat interface
4. The agent uses vector + keyword search to find relevant content
5. Responses include source citations

## Design Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| LLM | gpt-4o-mini | Fast + cost effective for 2-hour build |
| Embeddings | OpenAI (chroma fallback) | Best quality, auto-fallback works |
| Retrieval | Hybrid (vector + keyword) | Covers semantic + literal queries |
| Chunking | 1000 chars / 100 overlap | Configurable but works for most docs |
| Agent | ReAct | Transparent reasoning, can use multiple tools |

## Limitations (2-hour scope)

- No PDF support (would need PyPDF/pypdfium)
- No conversation memory (each query is independent)
- No streaming responses (simpler to implement)
- Single-session keyword index (resets on server restart)
