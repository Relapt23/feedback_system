from pydantic import BaseModel


class Feedback(BaseModel):
    text: str

class FeedbackAnswer(BaseModel):
    id: int
    status: str
    sentiment: str | None = None
    category: str