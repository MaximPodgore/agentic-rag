from typing import List, Dict, Any
import re
from collections import defaultdict


class KeywordSearcher:
    """BM25-style keyword search for documents."""

    def __init__(self):
        self.documents = []
        self.term_freqs = []
        self.doc_freqs = defaultdict(int)
        self.avg_doc_len = 0

    def index_documents(self, documents: List[str]) -> None:
        """Index documents for keyword search."""
        self.documents = documents
        self.term_freqs = []
        self.doc_freqs = defaultdict(int)
        total_len = 0

        for doc in documents:
            tokens = self.tokenize(doc)
            total_len += len(tokens)

            tf = defaultdict(int)
            seen_terms = set()
            for token in tokens:
                tf[token] += 1
                if token not in seen_terms:
                    seen_terms.add(token)
                    self.doc_freqs[token] += 1

            self.term_freqs.append(dict(tf))

        self.avg_doc_len = total_len / len(documents) if documents else 0

    def tokenize(self, text: str) -> List[str]:
        """Simple tokenization - lowercase words."""
        return re.findall(r'\b[a-zA-Z]+\b', text.lower())

    def search(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """
        BM25 search. Returns top k matching documents with scores.
        """
        if not self.documents:
            return []

        query_tokens = self.tokenize(query)
        if not query_tokens:
            return []

        scores = [0.0] * len(self.documents)
        k1 = 1.5
        b = 0.75

        for doc_idx, tf in enumerate(self.term_freqs):
            doc_len = sum(tf.values())
            score = 0.0

            for term in query_tokens:
                if term not in tf:
                    continue

                df = self.doc_freqs.get(term, 0)
                idf = (len(self.documents) - df + 0.5) / (df + 0.5)
                idf = max(0.1, idf)

                freq = tf[term]
                tf_component = (freq * (k1 + 1)) / (freq + k1 * (1 - b + b * doc_len / self.avg_doc_len))

                score += idf * tf_component

            scores[doc_idx] = score

        top_indices = sorted(range(len(scores)), key=lambda i: scores[i], reverse=True)[:top_k]

        results = []
        for idx in top_indices:
            if scores[idx] > 0:
                results.append({
                    "content": self.documents[idx],
                    "score": scores[idx],
                    "index": idx
                })

        return results
