from fastapi import APIRouter, Depends, HTTPException
from app.schemas import Feedback, FeedbackAnswer
from sqlalchemy.ext.asyncio import AsyncSession
from db.db_config import make_session
from db.models import FeedbackInfo
from datetime import datetime
from app.sentiment_analysis_api import analyze_sentiment

router = APIRouter()


@router.post("/feedback", response_model=FeedbackAnswer)
async def send_feedback(
    feedback: Feedback, session: AsyncSession = Depends(make_session)
):
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
    )
    session.add(feedback_info)
    await session.commit()
    await session.refresh(feedback_info)

    return FeedbackAnswer(
        id=feedback_info.id,
        status=feedback_info.status,
        sentiment=feedback_info.sentiment,
        category=feedback_info.category,
    )
