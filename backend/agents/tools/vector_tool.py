from langchain.tools import tool
from typing import Any, Dict
import sys
import os

# Add parent directories to path for imports
parent_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

from utils.chroma_store import ChromaStore


@tool
def vector_search(query: str, n_results: int = 5) -> str:
    """
    Search documents using vector/semantic similarity.
    Use this for:
    - Finding documents about concepts, ideas, or topics
    - Semantic queries where exact words might not match
    - Understanding the meaning or content of documents
    - Questions like "what do my notes say about..."

    Args:
        query: The search query in natural language
        n_results: Number of results to return (default 5)

    Returns:
        String containing search results with document content and metadata
    """
    store = ChromaStore()
    results = store.query(query, n_results=n_results)

    if not results or not results["documents"] or not results["documents"][0]:
        return "No results found."

    output = []
    for i, (doc, metadata, distance) in enumerate(zip(
        results["documents"][0],
        results["metadatas"][0],
        results["distances"][0]
    )):
        source = metadata.get("source", "unknown") if metadata else "unknown"
        score = 1 - distance if distance else 0
        output.append(f"[Result {i+1}] Source: {source} (similarity: {score:.3f})\n{doc}\n")

    return "\n".join(output)


@tool
def get_document_count() -> str:
    """
    Get the number of documents currently indexed.

    Returns:
        A message with the document count
    """
    store = ChromaStore()
    count = store.count()
    return f"There are {count} document chunks currently indexed."
