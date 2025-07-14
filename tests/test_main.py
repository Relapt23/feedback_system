import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import async_sessionmaker, AsyncSession, create_async_engine
from sqlalchemy import select
from db.db_config import make_session
from db.models import Base, FeedbackInfo
from main import app as fastapi_app
from httpx import AsyncClient, ASGITransport
import app.endpoints
from app.schemas import GeoLocationResponse
from datetime import datetime


@pytest_asyncio.fixture()
async def test_engine():
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:", connect_args={"check_same_thread": False}
    )
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    await engine.dispose()


@pytest_asyncio.fixture()
async def test_session(test_engine):
    test_sess = async_sessionmaker(bind=test_engine, expire_on_commit=False)

    async def override_session() -> AsyncSession:
        async with test_sess() as s:
            yield s

    fastapi_app.dependency_overrides[make_session] = override_session
    async with test_sess() as session:
        yield session
    fastapi_app.dependency_overrides.clear()


@pytest_asyncio.fixture()
async def client(test_session):
    async with AsyncClient(
        transport=ASGITransport(app=fastapi_app), base_url="http://test"
    ) as client:
        yield client


@pytest.mark.asyncio
async def test_send_feedback_success(client, monkeypatch, test_session):
    # given
    async def mock_get_geolocation(ip: str) -> GeoLocationResponse:
        return GeoLocationResponse(
            country="Canada",
            region="QC",
            city="Montreal",
            latitude=45.6026,
            longitude=-73.5167,
        )

    async def mock_analyze_sentiment(text: str) -> str:
        return "positive"

    async def mock_category_definition(text: str) -> str:
        return "оплата"

    # when
    monkeypatch.setattr(app.endpoints, "get_geolocation", mock_get_geolocation)
    monkeypatch.setattr(app.endpoints, "analyze_sentiment", mock_analyze_sentiment)
    monkeypatch.setattr(app.endpoints, "category_definition", mock_category_definition)

    response = await client.post(
        "/feedback", json={"text": "Excellent service for making payments"}
    )
    data = response.json()

    db_feedback = (
        await test_session.execute(
            select(FeedbackInfo).where(FeedbackInfo.id == data["id"])
        )
    ).scalar_one()

    # then
    assert response.status_code == 200
    assert isinstance(data["id"], int)
    assert data["status"] == "open"
    assert data["sentiment"] == "positive"
    assert data["category"] == "оплата"
    assert isinstance(data["ip"], str)
    assert data["country"] == "Canada"
    assert data["region"] == "QC"
    assert data["city"] == "Montreal"
    assert data["latitude"] == 45.6026
    assert data["longitude"] == -73.5167

    assert db_feedback.text == "Excellent service for making payments"
    assert db_feedback.status == "open"
    assert db_feedback.sentiment == "positive"
    assert db_feedback.category == "оплата"
    assert db_feedback.ip == data["ip"]
    assert db_feedback.country == "Canada"
    assert db_feedback.region == "QC"
    assert db_feedback.city == "Montreal"
    assert db_feedback.latitude == 45.6026
    assert db_feedback.longitude == -73.5167


@pytest.mark.asyncio
async def test_send_feedback_api_error(client, monkeypatch, test_session):
    # given
    async def mock_get_geolocation(ip: str) -> GeoLocationResponse:
        return GeoLocationResponse(
            country=None,
            region=None,
            city=None,
            latitude=None,
            longitude=None,
        )

    async def mock_analyze_sentiment(text: str) -> str:
        return "unknown"

    async def mock_category_definition(text: str) -> str:
        return "другое"

    # when
    monkeypatch.setattr(app.endpoints, "get_geolocation", mock_get_geolocation)
    monkeypatch.setattr(app.endpoints, "analyze_sentiment", mock_analyze_sentiment)
    monkeypatch.setattr(app.endpoints, "category_definition", mock_category_definition)

    response = await client.post("/feedback", json={"text": "kwckwkcwekc"})
    data = response.json()

    db_feedback = (
        await test_session.execute(
            select(FeedbackInfo).where(FeedbackInfo.id == data["id"])
        )
    ).scalar_one()

    # then
    assert response.status_code == 200
    assert isinstance(data["id"], int)
    assert data["sentiment"] == "unknown"
    assert data["status"] == "open"
    assert data["category"] == "другое"
    assert isinstance(data["ip"], str)
    assert data["country"] is None
    assert data["region"] is None
    assert data["city"] is None
    assert data["latitude"] is None
    assert data["longitude"] is None

    assert db_feedback.text == "kwckwkcwekc"
    assert db_feedback.status == "open"
    assert db_feedback.sentiment == "unknown"
    assert db_feedback.category == "другое"
    assert db_feedback.ip == data["ip"]
    assert db_feedback.country is None
    assert db_feedback.region is None
    assert db_feedback.city is None
    assert db_feedback.latitude is None
    assert db_feedback.longitude is None


@pytest.mark.asyncio
async def test_get_feedback_success(client, test_session):
    # given
    now = int(datetime.now().timestamp())
    old_ts = now - 3600
    test_session.add_all(
        [
            FeedbackInfo(
                text="A",
                status="open",
                timestamp=old_ts,
                sentiment="positive",
                category="техническая",
                ip="1.1.1.1",
                country="X",
                region="Y",
                city="Z",
                latitude=0.0,
                longitude=0.0,
            ),
            FeedbackInfo(
                text="B",
                status="open",
                timestamp=now,
                sentiment="negative",
                category="оплата",
                ip="1.1.1.2",
                country="X",
                region="Y",
                city="Z",
                latitude=0.0,
                longitude=0.0,
            ),
            FeedbackInfo(
                text="C",
                status="closed",
                timestamp=now,
                sentiment="negative",
                category="другое",
                ip="1.1.1.3",
                country="X",
                region="Y",
                city="Z",
                latitude=0.0,
                longitude=0.0,
            ),
        ]
    )
    await test_session.commit()

    # when
    response = await client.get(f"/feedback?status=open&timestamp={now}")

    # then
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["text"] == "B"


@pytest.mark.asyncio
async def test_feedback_closed(client, test_session):
    # given
    feedback = FeedbackInfo(
        text="B",
        status="open",
        timestamp=int(datetime.now().timestamp()),
        sentiment="negative",
        category="оплата",
        ip="1.1.1.2",
        country="X",
        region="Y",
        city="Z",
        latitude=0.0,
        longitude=0.0,
    )
    test_session.add(feedback)

    await test_session.commit()
    await test_session.refresh(feedback)

    # when
    response = await client.post(f"/feedback/close/{feedback.id}")
    data = response.json()
    await test_session.refresh(feedback)

    db_feedback = (
        await test_session.execute(
            select(FeedbackInfo).where(FeedbackInfo.id == feedback.id)
        )
    ).scalar_one()

    # then
    assert response.status_code == 200
    assert data["id"] == feedback.id
    assert data["status"] == "closed"
    assert db_feedback.status == "closed"
