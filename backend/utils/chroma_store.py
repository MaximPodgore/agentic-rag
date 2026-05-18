from typing import List, Dict, Any, Optional
import chromadb
from chromadb.utils import embedding_functions
import os

# Calculate chroma_data path relative to this file
DEFAULT_PERSIST_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "chroma_data"
)


class ChromaStore:
    """ChromaDB wrapper for document storage and retrieval."""

    def __init__(self, collection_name: str = "documents", persist_dir: str = None):
        if persist_dir is None:
            persist_dir = DEFAULT_PERSIST_DIR
        self.persist_dir = persist_dir
        os.makedirs(persist_dir, exist_ok=True)

        self.client = chromadb.PersistentClient(path=persist_dir)

        # Use OpenAI embeddings if key available, else default
        openai_key = os.getenv("OPENAI_API_KEY")
        if openai_key:
            self.embedding_fn = embedding_functions.OpenAIEmbeddingFunction(
                api_key=openai_key,
                model_name="text-embedding-3-small"
            )
        else:
            self.embedding_fn = embedding_functions.DefaultEmbeddingFunction()

        self.collection = self.client.get_or_create_collection(
            name=collection_name,
            embedding_function=self.embedding_fn
        )

    def add_documents(
        self,
        documents: List[str],
        metadatas: Optional[List[Dict[str, Any]]] = None,
        ids: Optional[List[str]] = None
    ) -> None:
        """Add documents to the collection."""
        if ids is None:
            ids = [f"doc_{i}" for i in range(len(documents))]

        batch_size = 100
        for i in range(0, len(documents), batch_size):
            batch_docs = documents[i:i + batch_size]
            batch_ids = ids[i:i + batch_size]
            batch_meta = metadatas[i:i + batch_size] if metadatas else None

            self.collection.add(
                documents=batch_docs,
                metadatas=batch_meta,
                ids=batch_ids
            )

    def query(self, query_text: str, n_results: int = 5) -> Dict[str, Any]:
        """Query the collection for similar documents."""
        results = self.collection.query(
            query_texts=[query_text],
            n_results=n_results
        )
        return results

    def get_all_documents(self) -> Dict[str, Any]:
        """Get all documents from the collection."""
        return self.collection.get()

    def count(self) -> int:
        """Get the number of documents in the collection."""
        return self.collection.count()

    def delete_all(self) -> None:
        """Delete all documents from the collection."""
        self.client.delete_collection("documents")
        self.collection = self.client.get_or_create_collection(
            name="documents",
            embedding_function=self.embedding_fn
        )
