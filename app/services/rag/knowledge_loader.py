"""
Knowledge Base Loader - Loads and chunks markdown documents for RAG.
"""

from pathlib import Path
from typing import List

from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_core.documents import Document

from app.config import get_settings, PROJECT_ROOT
from app.utils.logger import get_logger

logger = get_logger(__name__)


class KnowledgeLoader:
    """Loads markdown files from the knowledge base directory and chunks them."""

    def __init__(self):
        settings = get_settings()
        rag_config = settings.rag
        self._knowledge_dir = PROJECT_ROOT / rag_config.get("knowledge_dir", "config/knowledge_base")
        self._chunk_size = rag_config.get("chunk_size", 500)
        self._chunk_overlap = rag_config.get("chunk_overlap", 50)

    def load_and_chunk(self) -> List[Document]:
        """
        Load all markdown files from the knowledge base and split into chunks.

        Returns:
            List of Document objects with content and metadata.
        """
        documents = self._load_documents()
        chunks = self._split_documents(documents)

        logger.info(
            "knowledge_base_loaded",
            doc_count=len(documents),
            chunk_count=len(chunks),
            knowledge_dir=str(self._knowledge_dir),
        )

        return chunks

    def _load_documents(self) -> List[Document]:
        """Load all .md files from the knowledge directory."""
        documents = []
        knowledge_path = Path(self._knowledge_dir)

        if not knowledge_path.exists():
            logger.warning("knowledge_dir_not_found", path=str(knowledge_path))
            return documents

        for file_path in sorted(knowledge_path.glob("*.md")):
            try:
                content = file_path.read_text(encoding="utf-8")
                doc = Document(
                    page_content=content,
                    metadata={
                        "source": file_path.name,
                        "file_path": str(file_path),
                        "title": self._extract_title(content, file_path.stem),
                    },
                )
                documents.append(doc)
                logger.info("loaded_document", source=file_path.name, size=len(content))
            except Exception as e:
                logger.error("failed_to_load_document", file=str(file_path), error=str(e))

        return documents

    def _split_documents(self, documents: List[Document]) -> List[Document]:
        """Split documents into chunks using recursive character splitter."""
        splitter = RecursiveCharacterTextSplitter(
            chunk_size=self._chunk_size,
            chunk_overlap=self._chunk_overlap,
            length_function=len,
            separators=[
                "\n## ",   # H2 headers
                "\n### ",  # H3 headers
                "\n#### ", # H4 headers
                "\n\n",    # Paragraphs
                "\n",      # Lines
                ". ",      # Sentences
                " ",       # Words
            ],
        )

        chunks = splitter.split_documents(documents)

        # Add chunk index to metadata
        for i, chunk in enumerate(chunks):
            chunk.metadata["chunk_index"] = i

        return chunks

    def _extract_title(self, content: str, fallback: str) -> str:
        """Extract the title (first H1) from markdown content."""
        for line in content.split("\n"):
            line = line.strip()
            if line.startswith("# ") and not line.startswith("## "):
                return line[2:].strip()
        return fallback.replace("_", " ").title()
