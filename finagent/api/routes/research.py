from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy import select
from sqlalchemy.orm import Session

from finagent.agents.graph import research
from finagent.core.config import get_settings
from finagent.core.security import current_user
from finagent.db.models import Report, User
from finagent.db.session import get_db
from finagent.schemas.domain import ResearchRequest
from finagent.services.memory import ResearchMemory
from finagent.services.reports import render_pdf

router = APIRouter(prefix="/research", tags=["research"])


@router.post("")
def create_research(
    body: ResearchRequest, user: User = Depends(current_user), db: Session = Depends(get_db)
):
    recommendation = research(body, get_settings().market_data_mode)
    row = Report(
        user_id=user.id,
        ticker=body.ticker.upper(),
        recommendation=recommendation.action,
        score=recommendation.score,
        confidence=recommendation.confidence,
        thesis=recommendation.thesis,
        payload=recommendation.model_dump(mode="json"),
    )
    db.add(row)
    db.commit()
    ResearchMemory().add(row.id, row.ticker, row.thesis)
    return {"id": row.id, **recommendation.model_dump(mode="json")}


@router.get("")
def list_reports(user: User = Depends(current_user), db: Session = Depends(get_db)):
    rows = db.scalars(
        select(Report)
        .where(Report.user_id == user.id)
        .order_by(Report.created_at.desc())
        .limit(100)
    ).all()
    return [
        {
            "id": r.id,
            "ticker": r.ticker,
            "recommendation": r.recommendation,
            "score": r.score,
            "created_at": r.created_at,
        }
        for r in rows
    ]


@router.get("/{report_id}/pdf")
def pdf(report_id: str, user: User = Depends(current_user), db: Session = Depends(get_db)):
    row = db.scalar(select(Report).where(Report.id == report_id, Report.user_id == user.id))
    if not row:
        raise HTTPException(404, "Report not found")
    from finagent.schemas.domain import Recommendation

    content = render_pdf(row.ticker, Recommendation.model_validate(row.payload))
    return Response(
        content,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{row.ticker}-report.pdf"'},
    )
