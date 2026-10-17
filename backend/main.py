import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

try:
    from backend.database import init_db
    from backend.route import router
except ImportError:
    from database import init_db
    from route import router

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("querymind.api")


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Initializing QueryMind database schema...")
    init_db()
    logger.info("QueryMind API ready to handle requests.")
    yield
    logger.info("QueryMind API shutting down.")


app = FastAPI(
    title="QueryMind API",
    version="1.0.0",
    description="Autonomous Multi-Agent Research Assistant powered by LangGraph, Tavily, and Gemini.",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)
