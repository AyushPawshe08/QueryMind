import os
import logging
from typing import Generator
from dotenv import load_dotenv
from sqlalchemy import (
    create_engine,
    inspect,
    text,
)
from sqlalchemy.orm import sessionmaker, Session

try:
    from backend.model import Base, User, ResearchReport
except ImportError:
    from model import Base, User, ResearchReport

load_dotenv()

logger = logging.getLogger("querymind.database")


DATABASE_URL = os.getenv("DATABASE_URL", "").strip()
if not DATABASE_URL:
    raise RuntimeError(
        "DATABASE_URL is required. Set it to your Neon PostgreSQL connection string."
    )

if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql+psycopg2://", 1)
elif DATABASE_URL.startswith("postgresql://"):
    DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+psycopg2://", 1)
elif not DATABASE_URL.startswith("postgresql+psycopg2://"):
    raise ValueError(
        "DATABASE_URL must use PostgreSQL (for example, the Neon connection string)."
    )


engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,
    pool_recycle=300,
    pool_size=5,
    max_overflow=5,
)
logger.info("[Database] PostgreSQL engine configured for Neon.")

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def _migrate_research_reports_schema(connection):
    columns = {
        column["name"]
        for column in inspect(connection).get_columns("research_reports")
    }
    if "report_markdown" not in columns and "report" in columns:
        connection.execute(
            text(
                "ALTER TABLE research_reports "
                "RENAME COLUMN report TO report_markdown"
            )
        )
        logger.info("[Database] Renamed legacy research_reports.report column.")
        columns.add("report_markdown")

    if "status" not in columns:
        connection.execute(
            text(
                "ALTER TABLE research_reports "
                "ADD COLUMN status VARCHAR(50) NOT NULL DEFAULT 'completed'"
            )
        )
        logger.info("[Database] Added research_reports.status column.")


def init_db():
    """Create all tables in the configured database."""
    Base.metadata.create_all(bind=engine)
    with engine.begin() as connection:
        _migrate_research_reports_schema(connection)
    logger.info("[Database] All database tables initialized successfully.")


def get_db() -> Generator[Session, None, None]:
    """FastAPI Dependency for DB Session management."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
