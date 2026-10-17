from datetime import datetime, timezone

from sqlalchemy import Column, DateTime, ForeignKey, Integer, JSON, String, Text
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(100), nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    reports = relationship("ResearchReport", back_populates="user", cascade="all, delete-orphan")


class ResearchReport(Base):
    __tablename__ = "research_reports"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=True, index=True)
    topic = Column(String(500), nullable=False, index=True)
    sub_queries = Column(JSON, nullable=True, default=list)
    report_markdown = Column(Text, nullable=False)
    critique = Column(Text, nullable=True)
    score = Column(Integer, nullable=True, default=0)
    sources = Column(JSON, nullable=True, default=list)
    chart_data = Column(JSON, nullable=True, default=dict)
    iterations = Column(Integer, default=1)
    status = Column(String(50), default="completed")
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    user = relationship("User", back_populates="reports")
