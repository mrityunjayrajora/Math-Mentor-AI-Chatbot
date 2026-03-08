"""
Retriever - Hybrid retriever combining FAISS semantic search with BM25 reranking.
"""

from typing import List, Optional

from rank_bm25 import BM25Okapi
from langchain_core.documents import Document

from app.config import get_settings
from app.models.schemas import RetrievedChunk
from app.services.rag.vector_store import VectorStore
from app.utils.logger import get_logger

logger = get_logger(__name__)


class HybridRetriever:
    """
    Hybrid retriever that combines:
    1. FAISS semantic (dense) retrieval
    2. BM25 keyword (sparse) reranking

    Uses weighted fusion to combine scores from both methods.
    """

    def __init__(self, vector_store: VectorStore):
        settings = get_settings()
        rag_config = settings.rag

        self._vector_store = vector_store
        self._top_k = rag_config.get("top_k", 5)
        self._use_bm25 = rag_config.get("use_bm25_reranker", True)
        self._bm25_weight = rag_config.get("bm25_weight", 0.4)
        self._semantic_weight = rag_config.get("semantic_weight", 0.6)

        # BM25 index (built lazily from vector store documents)
        self._bm25_index: Optional[BM25Okapi] = None
        self._bm25_documents: List[Document] = []

    def build_bm25_index(self):
        """Build BM25 index from the documents in the vector store."""
        if not self._use_bm25:
            return

        docs = self._vector_store.get_all_documents()
        if not docs:
            logger.warning("no_documents_for_bm25")
            return

        self._bm25_documents = docs
        tokenized_corpus = [
            doc.page_content.lower().split() for doc in docs
        ]
        self._bm25_index = BM25Okapi(tokenized_corpus)
        logger.info("bm25_index_built", doc_count=len(docs))

    def retrieve(self, query: str, queries: Optional[List[str]] = None) -> List[RetrievedChunk]:
        """
        Retrieve relevant chunks using hybrid search (FAISS + BM25).

        Args:
            query: Primary search query.
            queries: Additional queries to search for (from intent router).

        Returns:
            List of RetrievedChunk objects, sorted by relevance.
        """
        all_queries = [query]
        if queries:
            all_queries.extend(queries)

        # Collect results from all queries
        semantic_results = {}
        bm25_results = {}

        for q in all_queries:
            # 1. FAISS semantic search
            faiss_results = self._vector_store.similarity_search(
                q, k=self._top_k * 2  # Fetch more for fusion
            )
            for doc, score in faiss_results:
                doc_key = doc.page_content[:100]  # Use content prefix as key
                # FAISS returns L2 distance (lower = better), convert to similarity
                similarity = 1.0 / (1.0 + score)
                if doc_key not in semantic_results or similarity > semantic_results[doc_key][1]:
                    semantic_results[doc_key] = (doc, similarity)

            # 2. BM25 search
            if self._use_bm25 and self._bm25_index is not None:
                bm25_scores = self._bm25_index.get_scores(q.lower().split())
                for i, bm25_score in enumerate(bm25_scores):
                    if bm25_score > 0 and i < len(self._bm25_documents):
                        doc = self._bm25_documents[i]
                        doc_key = doc.page_content[:100]
                        # Normalize BM25 score to 0-1
                        max_score = max(bm25_scores) if max(bm25_scores) > 0 else 1
                        normalized_score = bm25_score / max_score
                        if doc_key not in bm25_results or normalized_score > bm25_results[doc_key][1]:
                            bm25_results[doc_key] = (doc, normalized_score)

        # 3. Fuse scores
        fused_results = self._fuse_results(semantic_results, bm25_results)

        # 4. Sort by fused score and take top_k
        fused_results.sort(key=lambda x: x[1], reverse=True)
        top_results = fused_results[:self._top_k]

        # 5. Convert to RetrievedChunk
        chunks = []
        for doc, score in top_results:
            chunks.append(RetrievedChunk(
                content=doc.page_content,
                source=doc.metadata.get("source", "unknown"),
                relevance_score=round(score, 4),
            ))

        logger.info(
            "hybrid_retrieval_complete",
            query=query[:100],
            semantic_count=len(semantic_results),
            bm25_count=len(bm25_results),
            fused_count=len(chunks),
        )

        return chunks

    def _fuse_results(
        self,
        semantic: dict,
        bm25: dict,
    ) -> List[tuple]:
        """
        Fuse semantic and BM25 results using weighted combination.

        Returns:
            List of (Document, fused_score) tuples.
        """
        all_keys = set(semantic.keys()) | set(bm25.keys())
        fused = []

        for key in all_keys:
            semantic_score = semantic.get(key, (None, 0.0))[1]
            bm25_score = bm25.get(key, (None, 0.0))[1]

            # Get the document from whichever source has it
            doc = (
                semantic.get(key, (None,))[0]
                or bm25.get(key, (None,))[0]
            )

            if doc is None:
                continue

            # Weighted fusion
            if self._use_bm25:
                fused_score = (
                    self._semantic_weight * semantic_score
                    + self._bm25_weight * bm25_score
                )
            else:
                fused_score = semantic_score

            fused.append((doc, fused_score))

        return fused
