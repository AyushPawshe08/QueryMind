import os
import re
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any
from dotenv import load_dotenv

from sqlalchemy import (
    create_engine,
    text,
    Integer,
    String,
    Text,
    DateTime,
    ForeignKey,
    JSON,
    desc,
)
from sqlalchemy.orm import (
    DeclarativeBase,
    Mapped,
    mapped_column,
    relationship,
    sessionmaker,
    Session,
)

load_dotenv()


# ── SQLAlchemy Engine & Session Setup ──────────────────────────────────────────
def _get_database_url() -> str:
    raw_url = os.getenv("DATABASE_URL", "").strip("\"'")
    if not raw_url:
        return ""
    # Strip channel_binding if present (can cause handshake quirks on certain Windows libpq builds)
    clean_url = re.sub(r"[&?]channel_binding=[^&]+", "", raw_url)
    # Ensure SQLAlchemy psycopg2 driver prefix
    if clean_url.startswith("postgres://"):
        clean_url = clean_url.replace("postgres://", "postgresql+psycopg2://", 1)
    elif clean_url.startswith("postgresql://") and not clean_url.startswith("postgresql+"):
        clean_url = clean_url.replace("postgresql://", "postgresql+psycopg2://", 1)
    return clean_url


DB_URL = _get_database_url()

engine = None
SessionLocal = None

if DB_URL:
    try:
        engine = create_engine(
            DB_URL,
            pool_pre_ping=True,
            pool_recycle=300,
            pool_size=5,
            max_overflow=10,
        )
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    except Exception as e:
        print(f"[Database Error] Engine creation failed: {e}")


# ── Declarative Base & ORM Models ──────────────────────────────────────────────
class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    hashed_password: Mapped[str] = mapped_column(Text, nullable=False)
    full_name: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    reports: Mapped[List["ResearchReport"]] = relationship(
        "ResearchReport",
        back_populates="user",
        cascade="all, delete-orphan",
    )


class ResearchReport(Base):
    __tablename__ = "research_reports"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[Optional[int]] = mapped_column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )
    topic: Mapped[str] = mapped_column(Text, nullable=False)
    sub_queries: Mapped[Optional[Any]] = mapped_column(JSON, nullable=True)
    report: Mapped[str] = mapped_column(Text, nullable=False)
    critique: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    score: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    iterations: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    sources: Mapped[Optional[Any]] = mapped_column(JSON, nullable=True)
    chart_data: Mapped[Optional[Any]] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
        index=True,
    )

    user: Mapped[Optional["User"]] = relationship("User", back_populates="reports")


# ── Database Initialization & Migration ────────────────────────────────────────
def init_db() -> bool:
    """Initialize tables and apply non-destructive schema migrations via SQLAlchemy."""
    if not engine:
        print("[Database Notice] DATABASE_URL not configured.")
        return False

    try:
        # Create all tables (users, research_reports)
        Base.metadata.create_all(bind=engine)

        # Run non-destructive column additions for existing tables
        with engine.begin() as conn:
            conn.execute(text(
                "ALTER TABLE research_reports ADD COLUMN IF NOT EXISTS user_id INT "
                "REFERENCES users(id) ON DELETE CASCADE;"
            ))
            conn.execute(text(
                "ALTER TABLE research_reports ADD COLUMN IF NOT EXISTS chart_data JSONB;"
            ))
            conn.execute(text(
                "CREATE INDEX IF NOT EXISTS idx_reports_user_id ON research_reports (user_id);"
            ))
            conn.execute(text(
                "CREATE INDEX IF NOT EXISTS idx_reports_created_at ON research_reports (created_at DESC);"
            ))
        return True
    except Exception as e:
        print(f"[Database Error] init_db failed: {e}")
        return False


# ── User CRUD Operations ───────────────────────────────────────────────────────
def create_user(email: str, hashed_password: str, full_name: Optional[str] = None) -> Optional[Dict[str, Any]]:
    """Create a new user in the database."""
    if not SessionLocal:
        return None

    with SessionLocal() as session:
        try:
            # Check if user already exists
            existing = session.query(User).filter(User.email == email.lower().strip()).first()
            if existing:
                return None

            user = User(
                email=email.lower().strip(),
                hashed_password=hashed_password,
                full_name=full_name.strip() if full_name else None,
            )
            session.add(user)
            session.commit()
            session.refresh(user)
            return {
                "id": user.id,
                "email": user.email,
                "full_name": user.full_name,
                "created_at": user.created_at,
            }
        except Exception as e:
            session.rollback()
            print(f"[Database Error] create_user failed: {e}")
            return None


def get_user_by_email(email: str) -> Optional[Dict[str, Any]]:
    """Retrieve user record by email (including hashed_password for auth verification)."""
    if not SessionLocal:
        return None

    with SessionLocal() as session:
        try:
            user = session.query(User).filter(User.email == email.lower().strip()).first()
            if user:
                return {
                    "id": user.id,
                    "email": user.email,
                    "hashed_password": user.hashed_password,
                    "full_name": user.full_name,
                    "created_at": user.created_at,
                }
            return None
        except Exception as e:
            print(f"[Database Error] get_user_by_email failed: {e}")
            return None


def get_user_by_id(user_id: int) -> Optional[Dict[str, Any]]:
    """Retrieve user record by ID (excludes password)."""
    if not SessionLocal:
        return None

    with SessionLocal() as session:
        try:
            user = session.query(User).filter(User.id == user_id).first()
            if user:
                return {
                    "id": user.id,
                    "email": user.email,
                    "full_name": user.full_name,
                    "created_at": user.created_at,
                }
            return None
        except Exception as e:
            print(f"[Database Error] get_user_by_id failed: {e}")
            return None


# ── Report CRUD Operations (User-Scoped) ───────────────────────────────────────
def save_report(
    topic: str,
    sub_queries: List[str],
    report: str,
    critique: str,
    score: int,
    iterations: int,
    sources: List[str],
    chart_data: Optional[Dict[str, Any]] = None,
    user_id: Optional[int] = None,
) -> Optional[int]:
    """Save a research report associated with a user_id."""
    if not SessionLocal:
        return None

    with SessionLocal() as session:
        try:
            record = ResearchReport(
                user_id=user_id,
                topic=topic.strip(),
                sub_queries=sub_queries,
                report=report,
                critique=critique,
                score=score,
                iterations=iterations,
                sources=sources,
                chart_data=chart_data,
                created_at=datetime.now(timezone.utc),
            )
            session.add(record)
            session.commit()
            session.refresh(record)
            return record.id
        except Exception as e:
            session.rollback()
            print(f"[Database Error] save_report failed: {e}")
            return None


def get_past_reports(user_id: Optional[int] = None, limit: int = 30) -> List[Dict[str, Any]]:
    """
    Retrieve past research reports.
    If user_id is provided, only retrieves reports belonging to that user.
    """
    if not SessionLocal:
        return []

    with SessionLocal() as session:
        try:
            query = session.query(
                ResearchReport.id,
                ResearchReport.topic,
                ResearchReport.sub_queries,
                ResearchReport.score,
                ResearchReport.iterations,
                ResearchReport.created_at,
            )
            if user_id is not None:
                query = query.filter(ResearchReport.user_id == user_id)

            rows = query.order_by(desc(ResearchReport.created_at)).limit(limit).all()

            results = []
            for r in rows:
                results.append({
                    "id": r.id,
                    "topic": r.topic,
                    "sub_queries": r.sub_queries or [],
                    "score": r.score,
                    "iterations": r.iterations,
                    "created_at": r.created_at,
                })
            return results
        except Exception as e:
            print(f"[Database Error] get_past_reports failed: {e}")
            return []


def get_report_by_id(report_id: int, user_id: Optional[int] = None) -> Optional[Dict[str, Any]]:
    """
    Fetch a complete report record by its ID.
    If user_id is provided, enforces that the report belongs to that user.
    """
    if not SessionLocal:
        return None

    with SessionLocal() as session:
        try:
            query = session.query(ResearchReport).filter(ResearchReport.id == report_id)
            if user_id is not None:
                query = query.filter(ResearchReport.user_id == user_id)

            record = query.first()
            if record:
                return {
                    "id": record.id,
                    "user_id": record.user_id,
                    "topic": record.topic,
                    "sub_queries": record.sub_queries or [],
                    "report": record.report,
                    "critique": record.critique,
                    "score": record.score,
                    "iterations": record.iterations,
                    "sources": record.sources or [],
                    "chart_data": record.chart_data or {},
                    "created_at": record.created_at,
                }
            return None
        except Exception as e:
            print(f"[Database Error] get_report_by_id failed: {e}")
            return None


if __name__ == "__main__":
    print("Testing SQLAlchemy DB Initialization...")
    success = init_db()
    print(f"init_db() success: {success}")
