import os
import re
from pathlib import Path
from typing import List, Dict, Any


def load_documents(folder_path: str) -> List[Dict[str, Any]]:
    """
    Load all supported documents from a folder.
    Supports: .md, .txt
    Returns list of dicts with content, metadata, and id.
    """
    documents = []
    folder = Path(folder_path)

    for ext in ["*.md", "*.txt"]:
        for file_path in folder.rglob(ext):
            try:
                content = file_path.read_text(encoding="utf-8")
                chunks = chunk_text(content)

                for i, chunk in enumerate(chunks):
                    if chunk.strip():
                        doc = {
                            "content": chunk,
                            "metadata": {
                                "source": str(file_path),
                                "filename": file_path.name,
                                "chunk_index": i,
                                "file_type": file_path.suffix.lower()
                            },
                            "id": f"{file_path.stem}_{i}"
                        }
                        documents.append(doc)
            except Exception as e:
                print(f"Error reading {file_path}: {e}")

    return documents


def chunk_text(text: str, max_chunk_size: int = 1000, overlap: int = 100) -> List[str]:
    """
    Chunk text into overlapping segments.
    Uses paragraph boundaries where possible.
    """
    paragraphs = re.split(r'\n\s*\n', text)
    chunks = []
    current_chunk = ""

    for para in paragraphs:
        para = para.strip()
        if not para:
            continue

        if len(current_chunk) + len(para) > max_chunk_size and current_chunk:
            chunks.append(current_chunk.strip())
            words = current_chunk.split()
            overlap_text = " ".join(words[-overlap:]) if len(words) > overlap else current_chunk
            current_chunk = overlap_text + "\n\n" + para
        else:
            if current_chunk:
                current_chunk += "\n\n" + para
            else:
                current_chunk = para

    if current_chunk:
        chunks.append(current_chunk.strip())

    final_chunks = []
    for chunk in chunks:
        if len(chunk) > max_chunk_size * 1.5:
            for i in range(0, len(chunk), max_chunk_size - overlap):
                final_chunks.append(chunk[i:i + max_chunk_size])
        else:
            final_chunks.append(chunk)

    return final_chunks
