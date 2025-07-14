from pydantic import BaseModel, ConfigDict


class FeedbackRequest(BaseModel):
    text: str


class FeedbackResponse(BaseModel):
    id: int
    status: str
    sentiment: str
    category: str
    ip: str | None = None
    country: str | None = None
    region: str | None = None
    city: str | None = None
    latitude: float | None = None
    longitude: float | None = None

    model_config = ConfigDict(from_attributes=True)


class GeoLocationResponse(BaseModel):
    ip: str | None = None
    country: str | None = None
    region: str | None = None
    city: str | None = None
    latitude: float | None = None
    longitude: float | None = None


class FeedbackFullInfoResponse(BaseModel):
    id: int
    text: str
    status: str
    sentiment: str
    category: str
    ip: str | None = None
    country: str | None = None
    region: str | None = None
    city: str | None = None
    latitude: float | None = None
    longitude: float | None = None

    model_config = ConfigDict(from_attributes=True)
