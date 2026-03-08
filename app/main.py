"""
Math Mentor Backend - FastAPI Application Entry Point.
"""

import os
os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE" 

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.services.hitl.hitl_manager import HITLManager
from app.services.memory.memory_store import MemoryStore
from app.services.rag.knowledge_loader import KnowledgeLoader
from app.services.rag.retriever import HybridRetriever
from app.services.rag.vector_store import VectorStore
from app.services.pipeline import Pipeline
from app.utils.logger import setup_logging, get_logger

# Import routers
from app.routers import solve as solve_router
from app.routers import hitl as hitl_router
from app.routers import memory as memory_router


logger = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan: startup and shutdown logic."""
    global logger

    # --- Startup ---
    setup_logging()
    logger = get_logger("main")
    logger.info("starting_math_mentor_backend")

    settings = get_settings()

    # 1. Initialize vector store
    logger.info("initializing_vector_store")
    vector_store = VectorStore()

    # Try loading existing index, rebuild if not found
    if not vector_store.load_index():
        logger.info("building_vector_store_from_knowledge_base")
        loader = KnowledgeLoader()
        chunks = loader.load_and_chunk()
        if chunks:
            vector_store.build_index(chunks)
        else:
            logger.warning("no_knowledge_base_chunks_found")

    # 2. Initialize hybrid retriever (FAISS + BM25)
    logger.info("initializing_hybrid_retriever")
    retriever = HybridRetriever(vector_store)
    retriever.build_bm25_index()

    # 3. Initialize memory store
    logger.info("initializing_memory_store")
    memory_store = MemoryStore()

    # 4. Initialize HITL manager
    logger.info("initializing_hitl_manager")
    hitl_manager = HITLManager()

    # 5. Initialize pipeline
    logger.info("initializing_pipeline")
    pipeline = Pipeline(
        retriever=retriever,
        memory_store=memory_store,
        hitl_manager=hitl_manager,
    )

    # 6. Inject dependencies into routers
    solve_router.set_pipeline(pipeline)
    hitl_router.set_hitl_manager(hitl_manager)
    memory_router.set_memory_store(memory_store)

    logger.info("math_mentor_backend_ready")

    yield

    # --- Shutdown ---
    logger.info("shutting_down_math_mentor_backend")


# Create FastAPI app
app = FastAPI(
    title="Math Mentor API",
    description=(
        "Multimodal Math Mentor Backend — Solves JEE-style math problems "
        "using RAG + Multi-Agent System + HITL + Memory."
    ),
    version="1.0.0",
    lifespan=lifespan,
)

# CORS middleware
settings = get_settings()
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.server.get("cors_origins", ["*"]),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(solve_router.router)
app.include_router(hitl_router.router)
app.include_router(memory_router.router)


@app.get("/", tags=["health"])
async def root():
    """Root endpoint with API information."""
    return {
        "name": "Math Mentor API",
        "version": "1.0.0",
        "description": "Multimodal Math Mentor with RAG + Agents + HITL + Memory",
        "docs": "/docs",
        "endpoints": {
            "solve": "POST /api/solve",
            "hitl_pending": "GET /api/hitl/pending",
            "hitl_review": "POST /api/hitl/review",
            "hitl_status": "GET /api/hitl/{session_id}",
            "memory_similar": "GET /api/memory/similar",
            "memory_feedback": "POST /api/memory/feedback",
            "memory_stats": "GET /api/memory/stats",
        },
    }


@app.get("/health", tags=["health"])
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}
