from fastapi import APIRouter, Depends, HTTPException, Request
from app.schemas import FeedbackRequest, FeedbackResponse
from sqlalchemy.ext.asyncio import AsyncSession
from db.db_config import make_session
from db.models import FeedbackInfo
from datetime import datetime
from app.sentiment_analysis_api import analyze_sentiment
from app.geo_ip_api import get_geolocation
from app.gpt_api import category_definition

router = APIRouter()


@router.post("/feedback")
async def send_feedback(
    feedback: FeedbackRequest,
    request: Request,
    session: AsyncSession = Depends(make_session),
) -> FeedbackResponse:
    client_ip = request.client.host
    geo = await get_geolocation(client_ip)

    try:
        sentiment = await analyze_sentiment(feedback.text)
    except HTTPException:
        sentiment = "unknown"

    feedback_info = FeedbackInfo(
        text=feedback.text,
        status="open",
        timestamp=datetime.now().timestamp(),
        sentiment=sentiment,
        category="другое",
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

    category = await category_definition(feedback_info.text)
    feedback_info.category = category
    await session.commit()
    await session.refresh(feedback_info)

    return FeedbackResponse(
        id=feedback_info.id,
        status=feedback_info.status,
        sentiment=feedback_info.sentiment,
        category=feedback_info.category,
        ip=feedback_info.ip,
        country=feedback_info.country,
        region=feedback_info.region,
        city=feedback_info.city,
        latitude=feedback_info.latitude,
        longitude=feedback_info.longitude,
    )
