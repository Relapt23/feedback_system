from pydantic import BaseModel


class FeedbackRequest(BaseModel):
    text: str


class FeedbackResponse(BaseModel):
    id: int
    status: str
    sentiment: str | None = None
    category: str
