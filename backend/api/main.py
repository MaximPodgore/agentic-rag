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
from typing import List, Optional, Dict, Any
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


@app.post("/load-default")
def load_default_documents():
    """
    Load default documents from the documents folder.
    """
    default_docs_path = Path(backend_dir).parent / "documents"

    if not default_docs_path.exists():
        raise HTTPException(status_code=404, detail="Default documents folder not found")

    documents = load_documents(str(default_docs_path))

    if not documents:
        raise HTTPException(status_code=400, detail="No valid documents found in default folder")

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
        "message": f"Successfully loaded {len(documents)} document chunks from default folder",
        "files_processed": [d["metadata"]["filename"] for d in documents],
        "total_chunks": len(documents)
    }


@app.get("/test-questions")
def get_test_questions() -> List[str]:
    """
    Load test questions from the test_questions.txt file.
    """
    questions_path = Path(backend_dir).parent / "test_questions.txt"

    if not questions_path.exists():
        raise HTTPException(status_code=404, detail="Test questions file not found")

    content = questions_path.read_text(encoding="utf-8")
    questions = [q.strip() for q in content.split('\n') if q.strip()]

    return questions


# Global test state for incremental test running
test_state = {
    "running": False,
    "total": 0,
    "current": 0,
    "passed": 0,
    "failed": 0,
    "current_question": "",
    "results": [],
}


@app.post("/run-test")
def run_test() -> Dict[str, Any]:
    """
    Run the test by asking all test questions.
    Returns pass/fail based on whether all questions got valid responses.
    """
    questions_path = Path(backend_dir).parent / "test_questions.txt"

    if not questions_path.exists():
        raise HTTPException(status_code=404, detail="Test questions file not found")

    content = questions_path.read_text(encoding="utf-8")
    questions = [q.strip() for q in content.split('\n') if q.strip()]

    results = []
    passed_count = 0
    failed_count = 0

    for idx, question in enumerate(questions):
        print(f"Processing question {idx + 1}/{len(questions)}: {question[:50]}...")
        try:
            result = query_agent.query(question)
            print(f"  Result keys: {result.keys() if isinstance(result, dict) else 'not dict'}")
            answer = result.get("answer", "")
            sources = result.get("sources", [])

            print(f"  Answer length: {len(answer)}, Sources count: {len(sources)}")

            # Check if response is valid (not empty, not fallback, has sources)
            has_valid_answer = answer and answer != "No response generated" and len(answer) > 10
            has_sources = len(sources) > 0
            is_valid = has_valid_answer and has_sources

            if is_valid:
                passed_count += 1
                print(f"  PASSED")
            else:
                failed_count += 1
                print(f"  FAILED - has_answer: {has_valid_answer}, has_sources: {has_sources}")

            results.append({
                "question": question,
                "answer": answer[:200] + "..." if len(answer) > 200 else answer,
                "sources": sources,
                "passed": is_valid,
                "has_answer": has_valid_answer,
                "has_sources": has_sources
            })
        except Exception as e:
            print(f"  ERROR: {e}")
            failed_count += 1
            results.append({
                "question": question,
                "answer": f"Error: {str(e)}",
                "sources": [],
                "passed": False,
                "has_answer": False,
                "has_sources": False
            })

    return {
        "total_questions": len(questions),
        "passed": passed_count,
        "failed": failed_count,
        "all_passed": failed_count == 0,
        "results": results
    }


@app.post("/run-test-start")
def run_test_start() -> Dict[str, Any]:
    """
    Initialize a new incremental test run.
    """
    global test_state
    questions_path = Path(backend_dir).parent / "test_questions.txt"

    if not questions_path.exists():
        raise HTTPException(status_code=404, detail="Test questions file not found")

    content = questions_path.read_text(encoding="utf-8")
    questions = [q.strip() for q in content.split('\n') if q.strip()]

    test_state = {
        "running": True,
        "total": len(questions),
        "current": 0,
        "passed": 0,
        "failed": 0,
        "current_question": "",
        "results": [],
    }

    return {"status": "started", "total_questions": len(questions)}


@app.post("/run-test-next")
def run_test_next() -> Dict[str, Any]:
    """
    Run the next question in the incremental test.
    Returns the current progress.
    """
    global test_state

    if not test_state["running"]:
        raise HTTPException(status_code=400, detail="No test is running. Call /run-test-start first.")

    questions_path = Path(backend_dir).parent / "test_questions.txt"
    content = questions_path.read_text(encoding="utf-8")
    questions = [q.strip() for q in content.split('\n') if q.strip()]

    idx = test_state["current"]
    if idx >= len(questions):
        test_state["running"] = False
        return {
            "status": "complete",
            "total": test_state["total"],
            "current": test_state["current"],
            "passed": test_state["passed"],
            "failed": test_state["failed"],
            "all_passed": test_state["failed"] == 0,
        }

    question = questions[idx]
    test_state["current_question"] = question

    try:
        print(f"Processing question {idx + 1}/{test_state['total']}: {question[:50]}...")
        result = query_agent.query(question)
        answer = result.get("answer", "")
        sources = result.get("sources", [])

        print(f"  Answer length: {len(answer)}, Sources: {len(sources)}")

        # Check if response is valid (not empty, not fallback, has sources)
        has_valid_answer = answer and answer != "No response generated" and len(answer) > 10
        has_sources = len(sources) > 0
        is_valid = has_valid_answer and has_sources

        if is_valid:
            test_state["passed"] += 1
            print(f"  PASSED")
        else:
            test_state["failed"] += 1
            print(f"  FAILED - has_answer: {has_valid_answer}, has_sources: {has_sources}")

        question_result = {
            "question": question,
            "answer": answer[:200] + "..." if len(answer) > 200 else answer,
            "sources": sources,
            "passed": is_valid,
            "has_answer": has_valid_answer,
            "has_sources": has_sources
        }
        test_state["results"].append(question_result)
        test_state["current"] += 1

        return {
            "status": "running" if test_state["current"] < test_state["total"] else "complete",
            "total": test_state["total"],
            "current": test_state["current"],
            "passed": test_state["passed"],
            "failed": test_state["failed"],
            "question": question,
            "passed_this": is_valid,
        }
    except Exception as e:
        print(f"  ERROR: {e}")
        test_state["failed"] += 1
        test_state["results"].append({
            "question": question,
            "answer": f"Error: {str(e)}",
            "sources": [],
            "passed": False,
            "has_answer": False,
            "has_sources": False
        })
        test_state["current"] += 1

        return {
            "status": "running" if test_state["current"] < test_state["total"] else "complete",
            "total": test_state["total"],
            "current": test_state["current"],
            "passed": test_state["passed"],
            "failed": test_state["failed"],
            "question": question,
            "passed_this": False,
        }


@app.get("/run-test-status")
def run_test_status() -> Dict[str, Any]:
    """
    Get the current status of the running test.
    """
    return {
        "running": test_state["running"],
        "total": test_state["total"],
        "current": test_state["current"],
        "passed": test_state["passed"],
        "failed": test_state["failed"],
        "current_question": test_state["current_question"],
    }


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
