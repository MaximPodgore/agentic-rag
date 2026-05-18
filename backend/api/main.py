# Add backend directory to path for imports
import sys
import os

backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

os.chdir(backend_dir)

# Load environment variables from .env file
from dotenv import load_dotenv
load_dotenv(os.path.join(backend_dir, '.env'))

from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
import tempfile
import shutil
from pathlib import Path
import uvicorn

from agents.query_agent import QueryAgent
from utils.document_loader import load_documents
from utils.chroma_store import ChromaStore
from agents.tools.keyword_tool import set_indexed_documents

app = FastAPI(title="Agentic RAG API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global state
query_agent = QueryAgent()
chroma_store = ChromaStore()


class ChatRequest(BaseModel):
    message: str


class ChatResponse(BaseModel):
    answer: str
    sources: List[dict] = []


@app.get("/health")
def health_check():
    return {"status": "healthy", "documents_indexed": chroma_store.count()}


@app.post("/upload")
async def upload_documents(files: List[UploadFile] = File(...)):
    """
    Upload and index documents. Accepts .md, .txt, and .pdf files.
    """
    with tempfile.TemporaryDirectory() as temp_dir:
        saved_files = []

        for file in files:
            if not file.filename.endswith(('.md', '.txt', '.pdf', '.MD', '.TXT', '.PDF')):
                continue

            file_path = Path(temp_dir) / file.filename
            file_path.parent.mkdir(parents=True, exist_ok=True)

            with open(file_path, "wb") as f:
                shutil.copyfileobj(file.file, f)
            saved_files.append(file_path)

        # Load and chunk documents
        documents = load_documents(temp_dir)

        if not documents:
            import traceback
            from utils.document_loader import PDF_SUPPORT
            print(f"PDF_SUPPORT: {PDF_SUPPORT}")
            print(f"Saved files: {saved_files}")
            raise HTTPException(
                status_code=400,
                detail=f"No valid documents found. PDF_SUPPORT={PDF_SUPPORT}, files_saved={len(saved_files)}"
            )

        # Add to ChromaDB
        chroma_store.add_documents(
            documents=[d["content"] for d in documents],
            metadatas=[d["metadata"] for d in documents],
            ids=[d["id"] for d in documents]
        )

        # Set up keyword search
        set_indexed_documents(
            documents=[d["content"] for d in documents],
            metadatas=[d["metadata"] for d in documents]
        )

        return {
            "message": f"Successfully indexed {len(documents)} document chunks",
            "files_processed": [d["metadata"]["filename"] for d in documents],
            "total_chunks": len(documents)
        }


@app.post("/chat", response_model=ChatResponse)
def chat(request: ChatRequest):
    """
    Chat with the agent about indexed documents.
    """
    try:
        result = query_agent.query(request.message)

        # Format sources from the agent's sources_cited
        sources = []
        for source in result.get("sources", []):
            sources.append({"content": f"Source: {source}"})

        return ChatResponse(
            answer=result["answer"],
            sources=sources
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/clear")
def clear_documents():
    """
    Clear all indexed documents.
    """
    chroma_store.delete_all()
    return {"message": "All documents cleared"}


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
