import asyncio

from fastapi import APIRouter, Depends, Request, HTTPException
from app.schemas import FeedbackRequest, FeedbackResponse, FeedbackFullInfo
from sqlalchemy.ext.asyncio import AsyncSession
from db.db_config import make_session
from db.models import FeedbackInfo
from datetime import datetime
from app.sentiment_analysis_api import analyze_sentiment
from app.geo_ip_api import get_geolocation
from app.gpt_api import category_definition
from typing import List
from sqlalchemy import select, update

router = APIRouter()


@router.post("/feedback")
async def send_feedback(
    feedback: FeedbackRequest,
    request: Request,
    session: AsyncSession = Depends(make_session),
) -> FeedbackResponse:
    client_ip = request.client.host

    geo, sentiment, category = await asyncio.gather(
        get_geolocation(client_ip),
        analyze_sentiment(feedback.text),
        category_definition(feedback.text),
        return_exceptions=False,
    )

    feedback_info = FeedbackInfo(
        text=feedback.text,
        status="open",
        timestamp=datetime.now().timestamp(),
        sentiment=sentiment,
        category=category,
        ip=client_ip,
        country=geo.country,
        region=geo.region,
        city=geo.city,
        latitude=geo.latitude,
        longitude=geo.longitude,
    )
    session.add(feedback_info)
    await session.commit()
    await session.refresh(feedback_info)

    return FeedbackResponse.model_validate(feedback_info)


@router.get(
    "/feedback",
    summary="List feedbacks",
    description="Return feedbacks filtered by status and min timestamp",
)
async def get_feedbacks(
    status: str | None = None,
    timestamp: int | None = None,
    session: AsyncSession = Depends(make_session),
) -> List[FeedbackFullInfo]:
    query = select(FeedbackInfo)
    if status is not None:
        query = query.where(FeedbackInfo.status == status)
    if timestamp is not None:
        query = query.where(FeedbackInfo.timestamp >= timestamp)

    feedbacks = (await session.execute(query)).scalars().all()

    return [FeedbackFullInfo.model_validate(f) for f in feedbacks]


@router.post("/feedback/close/{feedback_id}")
async def close_feedback(
    feedback_id: int,
    session: AsyncSession = Depends(make_session),
) -> FeedbackResponse:
    update_feedback = (
        update(FeedbackInfo)
        .where(FeedbackInfo.id == feedback_id)
        .values(status="closed")
        .returning(FeedbackInfo)
    )

    feedback = (await session.scalars(update_feedback)).one_or_none()

    if feedback is None:
        raise HTTPException(detail="not_found", status_code=404)

    await session.commit()

    return FeedbackResponse.model_validate(feedback)
