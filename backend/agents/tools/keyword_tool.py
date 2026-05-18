from langchain.tools import tool
from typing import Any, Dict, List
import sys
import os

parent_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

from utils.keyword_search import KeywordSearcher

_keyword_searcher = KeywordSearcher()
_documents_indexed = False
_document_contents = []
_document_metadatas = []


def set_indexed_documents(documents: List[str], metadatas: List[Dict]) -> None:
    """Set the documents to be used for keyword search."""
    global _documents_indexed, _document_contents, _document_metadatas
    _document_contents = documents
    _document_metadatas = metadatas
    _keyword_searcher.index_documents(documents)
    _documents_indexed = True


@tool
def keyword_search(query: str, top_k: int = 5) -> str:
    """
    Search documents using keyword/BM25 matching.
    Use this for:
    - Finding specific words, names, or exact phrases
    - Queries with unique identifiers, file names, or specific terms
    - When you need literal word matching rather than semantic meaning
    - Questions like "find the file that mentions..."

    Args:
        query: The search query with keywords
        top_k: Number of results to return (default 5)

    Returns:
        String containing search results with document content and metadata
    """
    if not _documents_indexed:
        return "No documents indexed for keyword search yet. Please upload documents first."

    results = _keyword_searcher.search(query, top_k=top_k)

    if not results:
        return "No keyword matches found."

    output = []
    for i, result in enumerate(results):
        idx = result["index"]
        metadata = _document_metadatas[idx] if idx < len(_document_metadatas) else {}
        source = metadata.get("source", "unknown") if metadata else "unknown"
        filename = metadata.get("filename", source) if metadata else source
        output.append(f"[Result {i+1}] Source: {filename} (score: {result['score']:.3f})\n{result['content']}\n")

    return "\n".join(output)
