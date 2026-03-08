"""
Memory Store - SQLite-backed memory for solved problems with similarity search.
Supports self-learning through pattern reuse.
"""

import json
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import List, Optional

from langchain_google_genai import GoogleGenerativeAIEmbeddings
import numpy as np

from app.config import get_settings, PROJECT_ROOT
from app.models.enums import InputMode, MathTopic
from app.models.schemas import FeedbackRequest, MemoryEntry
from app.utils.logger import get_logger

logger = get_logger(__name__)


class MemoryStore:
    """
    SQLite-backed memory store for solved problems.
    Stores full pipeline records and provides similarity search
    via embedding comparison for self-learning.
    """

    def __init__(self):
        settings = get_settings()
        memory_config = settings.memory

        db_path = memory_config.get("db_path", "data/memory.db")
        self._db_path = PROJECT_ROOT / db_path
        self._similarity_threshold = memory_config.get("similarity_threshold", 0.75)
        self._max_results = memory_config.get("max_similar_results", 5)

        self._embeddings = GoogleGenerativeAIEmbeddings(
            model=settings.rag.get("embedding_model", "models/embedding-001"),
            google_api_key=settings.google_api_key,
        )

        self._init_db()

    def _init_db(self):
        """Initialize the SQLite database and create tables."""
        self._db_path.parent.mkdir(parents=True, exist_ok=True)

        conn = sqlite3.connect(str(self._db_path))
        cursor = conn.cursor()

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS memory (
                session_id TEXT PRIMARY KEY,
                input_mode TEXT,
                original_input TEXT,
                parsed_problem_text TEXT,
                topic TEXT,
                retrieved_context_summary TEXT,
                final_answer TEXT,
                solution_steps TEXT,
                explanation_summary TEXT DEFAULT '',
                verification_confidence REAL,
                is_correct INTEGER DEFAULT 1,
                user_feedback TEXT,
                user_feedback_correct INTEGER,
                embedding BLOB,
                created_at TEXT
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS ocr_corrections (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                original_text TEXT,
                corrected_text TEXT,
                created_at TEXT
            )
        """)

        # Migrate: add explanation_summary column if missing
        try:
            cursor.execute("ALTER TABLE memory ADD COLUMN explanation_summary TEXT DEFAULT ''")
        except sqlite3.OperationalError:
            pass  # Column already exists

        conn.commit()
        conn.close()

        logger.info("memory_db_initialized", path=str(self._db_path))

    def store(self, entry: MemoryEntry):
        """
        Store a solved problem in memory.

        Args:
            entry: MemoryEntry with all pipeline data.
        """
        try:
            # Generate embedding for the problem text
            embedding = self._embeddings.embed_query(entry.parsed_problem_text)
            embedding_blob = np.array(embedding, dtype=np.float32).tobytes()

            conn = sqlite3.connect(str(self._db_path))
            cursor = conn.cursor()

            cursor.execute(
                """
                INSERT OR REPLACE INTO memory
                (session_id, input_mode, original_input, parsed_problem_text,
                 topic, retrieved_context_summary, final_answer, solution_steps,
                 explanation_summary, verification_confidence, is_correct, user_feedback,
                 user_feedback_correct, embedding, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    entry.session_id,
                    entry.input_mode.value,
                    entry.original_input,
                    entry.parsed_problem_text,
                    entry.topic.value,
                    entry.retrieved_context_summary,
                    entry.final_answer,
                    json.dumps(entry.solution_steps),
                    entry.explanation_summary,
                    entry.verification_confidence,
                    1 if entry.is_correct else 0,
                    entry.user_feedback,
                    1 if entry.user_feedback_correct else (0 if entry.user_feedback_correct is False else None),
                    embedding_blob,
                    entry.created_at.isoformat(),
                ),
            )

            conn.commit()
            conn.close()

            logger.info("memory_stored", session_id=entry.session_id)

        except Exception as e:
            logger.error("memory_store_failed", error=str(e))

    def find_similar(self, query: str, top_k: Optional[int] = None) -> List[dict]:
        """
        Find similar previously solved problems using embedding similarity.

        Args:
            query: The problem text to search for.
            top_k: Number of results (defaults to config max_similar_results).

        Returns:
            List of similar problem records with similarity scores.
        """
        if top_k is None:
            top_k = self._max_results

        try:
            # Generate embedding for the query
            query_embedding = np.array(
                self._embeddings.embed_query(query), dtype=np.float32
            )

            conn = sqlite3.connect(str(self._db_path))
            cursor = conn.cursor()

            cursor.execute(
                "SELECT session_id, parsed_problem_text, topic, final_answer, "
                "solution_steps, explanation_summary, verification_confidence, is_correct, "
                "user_feedback, user_feedback_correct, embedding, created_at "
                "FROM memory WHERE embedding IS NOT NULL"
            )

            results = []
            for row in cursor.fetchall():
                stored_embedding = np.frombuffer(row[10], dtype=np.float32)

                # Cosine similarity
                similarity = float(
                    np.dot(query_embedding, stored_embedding)
                    / (np.linalg.norm(query_embedding) * np.linalg.norm(stored_embedding) + 1e-8)
                )

                if similarity >= self._similarity_threshold:
                    results.append({
                        "session_id": row[0],
                        "problem_text": row[1],
                        "topic": row[2],
                        "final_answer": row[3],
                        "solution_steps": json.loads(row[4]) if row[4] else [],
                        "explanation_summary": row[5] or "",
                        "verification_confidence": row[6],
                        "is_correct": bool(row[7]),
                        "user_feedback": row[8],
                        "user_feedback_correct": bool(row[9]) if row[9] is not None else None,
                        "similarity": similarity,
                        "created_at": row[11],
                    })

            conn.close()

            # Sort by similarity (highest first)
            results.sort(key=lambda x: x["similarity"], reverse=True)

            logger.info(
                "memory_search_complete",
                query=query[:100],
                matches=len(results),
                top_k=top_k,
            )

            return results[:top_k]

        except Exception as e:
            logger.error("memory_search_failed", error=str(e))
            return []

    def store_feedback(self, feedback: FeedbackRequest):
        """
        Store user feedback on a solved problem.

        Args:
            feedback: FeedbackRequest with session_id, is_correct, and comment.
        """
        try:
            conn = sqlite3.connect(str(self._db_path))
            cursor = conn.cursor()

            cursor.execute(
                """
                UPDATE memory
                SET user_feedback = ?, user_feedback_correct = ?
                WHERE session_id = ?
                """,
                (
                    feedback.comment,
                    1 if feedback.is_correct else 0,
                    feedback.session_id,
                ),
            )

            conn.commit()
            conn.close()

            logger.info(
                "feedback_stored",
                session_id=feedback.session_id,
                is_correct=feedback.is_correct,
            )

        except Exception as e:
            logger.error("feedback_store_failed", error=str(e))

    def store_ocr_correction(self, original: str, corrected: str):
        """Store an OCR correction for future pattern matching."""
        try:
            conn = sqlite3.connect(str(self._db_path))
            cursor = conn.cursor()

            cursor.execute(
                "INSERT INTO ocr_corrections (original_text, corrected_text, created_at) "
                "VALUES (?, ?, ?)",
                (original, corrected, datetime.utcnow().isoformat()),
            )

            conn.commit()
            conn.close()

            logger.info("ocr_correction_stored")

        except Exception as e:
            logger.error("ocr_correction_store_failed", error=str(e))

    def get_ocr_corrections(self) -> List[dict]:
        """Retrieve all stored OCR corrections for pattern reuse."""
        try:
            conn = sqlite3.connect(str(self._db_path))
            cursor = conn.cursor()

            cursor.execute(
                "SELECT original_text, corrected_text FROM ocr_corrections"
            )

            corrections = [
                {"original": row[0], "corrected": row[1]}
                for row in cursor.fetchall()
            ]

            conn.close()
            return corrections

        except Exception as e:
            logger.error("ocr_corrections_fetch_failed", error=str(e))
            return []

    def list_problems(self, page: int = 1, per_page: int = 20, topic: Optional[str] = None) -> dict:
        """
        List all solved problems with pagination and optional topic filter.

        Returns:
            dict with 'problems', 'total', 'page', 'per_page', 'total_pages'.
        """
        try:
            conn = sqlite3.connect(str(self._db_path))
            cursor = conn.cursor()

            # Count total
            if topic:
                cursor.execute("SELECT COUNT(*) FROM memory WHERE topic = ?", (topic,))
            else:
                cursor.execute("SELECT COUNT(*) FROM memory")
            total = cursor.fetchone()[0]

            # Fetch page
            offset = (page - 1) * per_page
            if topic:
                cursor.execute(
                    "SELECT session_id, input_mode, parsed_problem_text, topic, "
                    "final_answer, solution_steps, explanation_summary, verification_confidence, is_correct, "
                    "user_feedback, created_at "
                    "FROM memory WHERE topic = ? ORDER BY created_at DESC LIMIT ? OFFSET ?",
                    (topic, per_page, offset),
                )
            else:
                cursor.execute(
                    "SELECT session_id, input_mode, parsed_problem_text, topic, "
                    "final_answer, solution_steps, explanation_summary, verification_confidence, is_correct, "
                    "user_feedback, created_at "
                    "FROM memory ORDER BY created_at DESC LIMIT ? OFFSET ?",
                    (per_page, offset),
                )

            problems = []
            for row in cursor.fetchall():
                problems.append({
                    "session_id": row[0],
                    "input_mode": row[1],
                    "problem_text": row[2],
                    "topic": row[3],
                    "final_answer": row[4],
                    "solution_steps": json.loads(row[5]) if row[5] else [],
                    "explanation": row[6] or "",
                    "verification_confidence": row[7],
                    "is_correct": bool(row[8]),
                    "user_feedback": row[9],
                    "created_at": row[10],
                })

            conn.close()

            import math
            total_pages = math.ceil(total / per_page) if per_page > 0 else 0

            return {
                "problems": problems,
                "total": total,
                "page": page,
                "per_page": per_page,
                "total_pages": total_pages,
            }

        except Exception as e:
            logger.error("memory_list_failed", error=str(e))
            return {"problems": [], "total": 0, "page": page, "per_page": per_page, "total_pages": 0}

    def get_stats(self) -> dict:
        """Get memory store statistics."""
        try:
            conn = sqlite3.connect(str(self._db_path))
            cursor = conn.cursor()

            cursor.execute("SELECT COUNT(*) FROM memory")
            total = cursor.fetchone()[0]

            cursor.execute("SELECT COUNT(*) FROM memory WHERE is_correct = 1")
            correct = cursor.fetchone()[0]

            cursor.execute("SELECT COUNT(*) FROM memory WHERE user_feedback_correct IS NOT NULL")
            feedback_count = cursor.fetchone()[0]

            cursor.execute("SELECT COUNT(*) FROM ocr_corrections")
            ocr_corrections = cursor.fetchone()[0]

            conn.close()

            return {
                "total_problems": total,
                "correct_problems": correct,
                "feedback_count": feedback_count,
                "ocr_corrections": ocr_corrections,
                "accuracy": correct / total if total > 0 else 0,
            }

        except Exception as e:
            logger.error("memory_stats_failed", error=str(e))
            return {}

    def delete_problem(self, session_id: str) -> bool:
        """Delete a specific problem from memory."""
        try:
            conn = sqlite3.connect(str(self._db_path))
            cursor = conn.cursor()
            cursor.execute("DELETE FROM memory WHERE session_id = ?", (session_id,))
            deleted = cursor.rowcount > 0
            conn.commit()
            conn.close()
            logger.info("memory_problem_deleted", session_id=session_id)
            return deleted
        except Exception as e:
            logger.error("memory_delete_failed", error=str(e))
            return False

    def clear_all(self) -> int:
        """Clear all problems from memory. Returns count of deleted items."""
        try:
            conn = sqlite3.connect(str(self._db_path))
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM memory")
            count = cursor.fetchone()[0]
            cursor.execute("DELETE FROM memory")
            conn.commit()
            conn.close()
            logger.info("memory_cleared", count=count)
            return count
        except Exception as e:
            logger.error("memory_clear_failed", error=str(e))
            return 0
