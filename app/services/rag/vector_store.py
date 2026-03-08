"""
Vector Store - FAISS-based vector store with Google embeddings.
"""

from pathlib import Path
from typing import List, Optional

from langchain_core.documents import Document
from langchain_google_genai import GoogleGenerativeAIEmbeddings

from app.config import get_settings, PROJECT_ROOT
from app.utils.logger import get_logger

logger = get_logger(__name__)


class VectorStore:
    """
    FAISS vector store for storing and retrieving knowledge base chunks.
    Uses Google Generative AI embeddings.
    """

    def __init__(self):
        settings = get_settings()
        rag_config = settings.rag

        self._embedding_model = GoogleGenerativeAIEmbeddings(
            model=rag_config.get("embedding_model", "models/embedding-001"),
            google_api_key=settings.google_api_key,
        )
        self._persist_dir = PROJECT_ROOT / "data" / "vector_store"
        self._store = None  # Lazy-loaded FAISS index

    def build_index(self, chunks: List[Document]):
        """
        Build a FAISS index from document chunks.

        Args:
            chunks: List of Document objects to index.
        """
        from langchain_community.vectorstores import FAISS

        if not chunks:
            logger.warning("no_chunks_to_index")
            return

        logger.info("building_faiss_index", chunk_count=len(chunks))
        self._store = FAISS.from_documents(chunks, self._embedding_model)

        # Persist to disk
        self._persist_dir.mkdir(parents=True, exist_ok=True)
        self._store.save_local(str(self._persist_dir))
        logger.info("faiss_index_built_and_saved", path=str(self._persist_dir))

    def load_index(self) -> bool:
        """
        Load a persisted FAISS index from disk.

        Returns:
            True if loaded successfully, False otherwise.
        """
        from langchain_community.vectorstores import FAISS

        index_path = self._persist_dir / "index.faiss"
        if not index_path.exists():
            logger.info("no_persisted_index_found", path=str(index_path))
            return False

        try:
            self._store = FAISS.load_local(
                str(self._persist_dir),
                self._embedding_model,
                allow_dangerous_deserialization=True,
            )
            logger.info("faiss_index_loaded", path=str(self._persist_dir))
            return True
        except Exception as e:
            logger.error("failed_to_load_index", error=str(e))
            return False

    def similarity_search(
        self, query: str, k: int = 5
    ) -> List[tuple]:
        """
        Search the vector store for similar documents.

        Args:
            query: The search query.
            k: Number of results to return.

        Returns:
            List of (Document, score) tuples.
        """
        if self._store is None:
            logger.warning("vector_store_not_initialized")
            return []

        try:
            results = self._store.similarity_search_with_score(query, k=k)
            logger.info("similarity_search", query=query[:100], result_count=len(results))
            return results
        except Exception as e:
            logger.error("similarity_search_failed", error=str(e))
            return []

    @property
    def is_initialized(self) -> bool:
        return self._store is not None

    def get_all_documents(self) -> List[Document]:
        """Get all documents in the store (for BM25 indexing)."""
        if self._store is None:
            return []
        # FAISS docstore stores all documents
        try:
            docs = []
            for doc_id in self._store.docstore._dict:
                docs.append(self._store.docstore._dict[doc_id])
            return docs
        except Exception:
            return []
