import asyncio
import json
import logging
from datetime import datetime, timezone
from typing import Any, Dict, Optional, List

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import StreamingResponse, PlainTextResponse
from sqlalchemy.orm import Session

try:
    from backend.database import get_db, User, ResearchReport
    from backend.schemas import (
        UserRegisterSchema,
        UserLoginSchema,
        UserResponseSchema,
        TokenResponseSchema,
        TopicValidationRequest,
        TopicValidationResponse,
        ResearchRequest,
        ResearchResponse,
        ReportListItem,
        ReportDetailResponse,
    )
    from backend.auth import (
        hash_password,
        verify_password,
        create_access_token,
        get_current_user,
        get_optional_current_user,
    )
    from backend.graph import research_graph
    from backend.agent import validate_topic
except ImportError:
    from database import get_db, User, ResearchReport
    from schemas import (
        UserRegisterSchema,
        UserLoginSchema,
        UserResponseSchema,
        TokenResponseSchema,
        TopicValidationRequest,
        TopicValidationResponse,
        ResearchRequest,
        ResearchResponse,
        ReportListItem,
        ReportDetailResponse,
    )
    from auth import (
        hash_password,
        verify_password,
        create_access_token,
        get_current_user,
        get_optional_current_user,
    )
    from graph import research_graph
    from agent import validate_topic

logger = logging.getLogger("querymind.api")
router = APIRouter()


def _save_research_report(
    db: Session,
    *,
    user_id: Optional[int],
    topic: str,
    state: Dict[str, Any],
) -> ResearchReport:
    try:
        report_record = ResearchReport(
            user_id=user_id,
            topic=topic,
            sub_queries=state.get("sub_queries", []),
            report_markdown=state.get("report", ""),
            critique=state.get("critique", ""),
            score=state.get("score", 0),
            sources=state.get("sources", []),
            chart_data=state.get("chart_data", {}),
            iterations=state.get("iterations", 1),
            status="completed",
        )
        db.add(report_record)
        db.commit()
        db.refresh(report_record)
        return report_record
    except Exception as exc:
        db.rollback()
        logger.exception("Failed to save research report to DB.")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Research completed, but the report could not be saved.",
        ) from exc


# ── Health & Diagnostics ───────────────────────────────────────────────────────
@router.get("/", tags=["General"])
def root():
    return {
        "name": "QueryMind API",
        "version": "1.0.0",
        "status": "online",
        "docs_url": "/docs",
    }


@router.get("/health", tags=["General"])
def health():
    return {
        "status": "healthy",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


@router.post("/auth/register", response_model=TokenResponseSchema, status_code=status.HTTP_201_CREATED, tags=["Auth"])
def register_user(payload: UserRegisterSchema, db: Session = Depends(get_db)):
    existing_user = db.query(User).filter(User.email == payload.email).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="An account with this email address already exists.",
        )

    hashed_pw = hash_password(payload.password)
    user = User(
        email=payload.email,
        hashed_password=hashed_pw,
        full_name=payload.full_name,
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    token = create_access_token(user_id=user.id, email=user.email)
    return {
        "access_token": token,
        "token_type": "bearer",
        "user": user,
    }


@router.post("/auth/login", response_model=TokenResponseSchema, tags=["Auth"])
def login_user(payload: UserLoginSchema, db: Session = Depends(get_db)):
    """Authenticate existing user credentials and return a signed JWT token."""
    user = db.query(User).filter(User.email == payload.email).first()
    if not user or not verify_password(payload.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = create_access_token(user_id=user.id, email=user.email)
    return {
        "access_token": token,
        "token_type": "bearer",
        "user": user,
    }


@router.get("/auth/me", response_model=UserResponseSchema, tags=["Auth"])
def get_current_user_profile(current_user: User = Depends(get_current_user)):
    """Retrieve profile details for the authenticated user."""
    return current_user


@router.post("/research/validate", response_model=TopicValidationResponse, tags=["Research"])
def validate_research_topic(payload: TopicValidationRequest):
    """
    Validate whether the given topic is suitable for factual, multi-agent web research.
    Filters out purely subjective or vague prompts.
    """
    result = validate_topic(payload.topic.strip())
    return TopicValidationResponse(
        valid=result.get("valid", True),
        reason=result.get("reason", ""),
    )


@router.post("/research", response_model=ResearchResponse, tags=["Research"])
async def run_research(
    payload: ResearchRequest,
    current_user: Optional[User] = Depends(get_optional_current_user),
    db: Session = Depends(get_db),
):
    """
    Execute autonomous multi-agent deep research synchronously.
    Runs the Planner -> Search -> Reader -> Writer -> Critic pipeline.
    Optionally saves the final report to PostgreSQL / SQLite.
    """
    topic = payload.topic.strip()
    if not topic:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Topic cannot be empty.")

    validation = await asyncio.to_thread(validate_topic, topic)
    if not validation.get("valid", False):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=validation.get("reason") or "This topic is not suitable for research.",
        )

    initial_state = {
        "topic": topic,
        "sub_queries": [],
        "search_results": "",
        "scraped_content": "",
        "sources": [],
        "report": "",
        "critique": "",
        "score": 0,
        "iterations": 0,
        "chart_data": {},
    }

    try:
        # Run research graph to completion
        final_state = await asyncio.to_thread(research_graph.invoke, initial_state)
    except Exception as exc:
        logger.exception("Error executing research pipeline: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Research agent encountered an error: {str(exc)}",
        )

    report_record = None
    if payload.save_to_history:
        report_record = _save_research_report(
            db,
            user_id=current_user.id if current_user else None,
            topic=topic,
            state=final_state,
        )

    return ResearchResponse(
        id=report_record.id if report_record else None,
        topic=topic,
        report=final_state.get("report", ""),
        critique=final_state.get("critique", ""),
        score=final_state.get("score", 0),
        sources=final_state.get("sources", []),
        chart_data=final_state.get("chart_data", {}),
        sub_queries=final_state.get("sub_queries", []),
        iterations=final_state.get("iterations", 1),
        created_at=report_record.created_at if report_record else datetime.now(timezone.utc),
    )


@router.get("/research/stream", tags=["Research"])
async def stream_research(
    topic: str = Query(..., min_length=2, max_length=500, description="Research topic"),
    save: bool = Query(default=True, description="Save result to database"),
    token: Optional[str] = Query(default=None, description="Optional JWT token for saving to user history"),
    db: Session = Depends(get_db),
):
    """
    Stream live agent execution events using Server-Sent Events (SSE).
    Emits events as the agents step through Planner, Search, Read, Write, and Critic.
    """
    try:
        from backend.auth import decode_access_token
    except ImportError:
        from auth import decode_access_token

    # Resolve optional user from query token
    user_id = None
    if token:
        payload = decode_access_token(token)
        if payload:
            user_id = payload.get("user_id")

    topic = topic.strip()
    validation = await asyncio.to_thread(validate_topic, topic)
    if not validation.get("valid", False):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=validation.get("reason") or "This topic is not suitable for research.",
        )

    async def event_generator():
        initial_state = {
            "topic": topic,
            "sub_queries": [],
            "search_results": "",
            "scraped_content": "",
            "sources": [],
            "report": "",
            "critique": "",
            "score": 0,
            "iterations": 0,
            "chart_data": {},
        }

        # 1. Start event
        yield f"event: start\ndata: {json.dumps({'message': 'Initializing research pipeline...', 'topic': topic})}\n\n"

        final_state = dict(initial_state)

        def run_streaming():
            events = []
            for node_update in research_graph.stream(initial_state, stream_mode="updates"):
                events.append(node_update)
            return events

        try:
            # Run stream execution in threadpool to prevent blocking FastAPI event loop
            node_updates = await asyncio.to_thread(run_streaming)

            for update in node_updates:
                for node_name, state_patch in update.items():
                    final_state.update(state_patch)

                    event_payload = {
                        "node": node_name,
                        "iterations": final_state.get("iterations", 0),
                        "score": final_state.get("score"),
                    }

                    if node_name == "planner":
                        event_payload["message"] = f"Decomposed query into {len(state_patch.get('sub_queries', []))} orthogonal angles."
                        event_payload["sub_queries"] = state_patch.get("sub_queries", [])
                    elif node_name == "search":
                        event_payload["message"] = f"Gathered intelligence from {len(state_patch.get('sources', []))} verified web sources."
                        event_payload["sources"] = state_patch.get("sources", [])
                    elif node_name == "read":
                        event_payload["message"] = "Deep scraped and retrieved the most information-dense paragraphs via RAG."
                    elif node_name == "write":
                        event_payload["message"] = "Synthesized authoritative report and generated architectural diagrams."
                        event_payload["chart_data"] = state_patch.get("chart_data", {})
                    elif node_name == "critic":
                        event_payload["message"] = f"Critic reviewed quality: Score {state_patch.get('score')}/10."
                        event_payload["critique"] = state_patch.get("critique", "")

                    yield f"event: step\ndata: {json.dumps(event_payload)}\n\n"
                    await asyncio.sleep(0.05)

            # Persist to DB if requested
            report_id = None
            if save:
                try:
                    report_record = _save_research_report(
                        db,
                        user_id=user_id,
                        topic=topic,
                        state=final_state,
                    )
                    report_id = report_record.id
                except HTTPException as exc:
                    yield f"event: error\ndata: {json.dumps({'error': exc.detail})}\n\n"
                    return

            # Emit final complete event
            complete_payload = {
                "id": report_id,
                "topic": topic,
                "report": final_state.get("report", ""),
                "critique": final_state.get("critique", ""),
                "score": final_state.get("score", 0),
                "sources": final_state.get("sources", []),
                "chart_data": final_state.get("chart_data", {}),
                "sub_queries": final_state.get("sub_queries", []),
                "iterations": final_state.get("iterations", 1),
            }
            yield f"event: complete\ndata: {json.dumps(complete_payload)}\n\n"

        except Exception as exc:
            logger.exception("Error in SSE research stream: %s", exc)
            yield f"event: error\ndata: {json.dumps({'error': str(exc)})}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@router.get("/reports", response_model=List[ReportListItem], tags=["Reports"])
def list_user_reports(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Retrieve history of research reports created by the authenticated user."""
    reports = (
        db.query(ResearchReport)
        .filter(ResearchReport.user_id == current_user.id)
        .order_by(ResearchReport.created_at.desc())
        .all()
    )
    return reports


@router.get("/reports/{report_id}", response_model=ReportDetailResponse, tags=["Reports"])
def get_report_detail(
    report_id: int,
    current_user: Optional[User] = Depends(get_optional_current_user),
    db: Session = Depends(get_db),
):
    """Fetch complete research report details by ID."""
    report = db.query(ResearchReport).filter(ResearchReport.id == report_id).first()
    if not report:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Report not found.")

    # If the report belongs to a registered user, ensure requester owns it
    if report.user_id is not None and (not current_user or current_user.id != report.user_id):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied.")

    return report


@router.delete("/reports/{report_id}", status_code=status.HTTP_204_NO_CONTENT, tags=["Reports"])
def delete_report(
    report_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Delete a report owned by the authenticated user."""
    report = db.query(ResearchReport).filter(ResearchReport.id == report_id).first()
    if not report:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Report not found.")

    if report.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied.")

    db.delete(report)
    db.commit()
    return None


@router.get("/reports/{report_id}/markdown", response_class=PlainTextResponse, tags=["Reports"])
def download_report_markdown(
    report_id: int,
    db: Session = Depends(get_db),
):
    """Download the raw Markdown content of a research report."""
    report = db.query(ResearchReport).filter(ResearchReport.id == report_id).first()
    if not report:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Report not found.")

    filename = f"report_{report_id}.md"
    return PlainTextResponse(
        content=report.report_markdown,
        media_type="text/markdown",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
