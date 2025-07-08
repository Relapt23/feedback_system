import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import async_sessionmaker, AsyncSession, create_async_engine
from db.db_config import make_session
from db.models import Base
from main import app as fastapi_app
from httpx import AsyncClient, ASGITransport
import app.endpoints
from fastapi import HTTPException


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
        async with test_sess() as session:
            yield session

    fastapi_app.dependency_overrides[make_session] = override_session
    yield
    fastapi_app.dependency_overrides.clear()


@pytest_asyncio.fixture()
async def client(test_session):
    async with AsyncClient(
        transport=ASGITransport(app=fastapi_app), base_url="http://test"
    ) as client:
        yield client


@pytest.mark.asyncio
async def test_send_feedback_success(client, monkeypatch):
    # given
    async def mock_analyze_sentiment(text: str) -> str:
        return "positive"

    # when
    monkeypatch.setattr(app.endpoints, "analyze_sentiment", mock_analyze_sentiment)

    response = await client.post("/feedback", json={"text": "Nice service"})

    # then
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data["id"], int)
    assert data["status"] == "open"
    assert data["sentiment"] == "positive"
    assert data["category"] == "другое"


@pytest.mark.asyncio
async def test_send_feedback_api_error(client, monkeypatch):
    # given
    async def mock_analyze_sentiment(text: str) -> str:
        raise HTTPException(status_code=502, detail="Sentiment API error")

    # when
    monkeypatch.setattr(app.endpoints, "analyze_sentiment", mock_analyze_sentiment)
    response = await client.post("/feedback", json={"text": "kwckwkcwekc"})
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data["id"], int)
    assert data["sentiment"] == "unknown"
    assert data["status"] == "open"
    assert data["category"] == "другое"
