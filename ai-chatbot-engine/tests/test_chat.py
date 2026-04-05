"""Tests for AI Chatbot Engine."""
import pytest
from httpx import AsyncClient, ASGITransport
from main import app, Config
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
import os

# Use in-memory DB for tests
TEST_DB = "sqlite+aiosqlite:///:memory:"
os.environ["DATABASE_URL"] = TEST_DB

test_engine = create_async_engine(TEST_DB, echo=False)
TestSession = async_sessionmaker(test_engine, class_=AsyncSession, expire_on_commit=False)


@pytest.fixture(autouse=True)
async def setup_db():
    from main import Base
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest.fixture
async def client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest.mark.asyncio
async def test_health(client):
    resp = await client.get("/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "ok"
    assert "timestamp" in data


@pytest.mark.asyncio
async def test_list_threads_empty(client):
    resp = await client.get("/api/v1/threads")
    assert resp.status_code == 200
    assert resp.json() == []


@pytest.mark.asyncio
async def test_chat_requires_message(client):
    resp = await client.post("/api/v1/chat", json={})
    assert resp.status_code == 422  # Validation error


@pytest.mark.asyncio
async def test_invalid_thread_404(client):
    resp = await client.post("/api/v1/chat", json={
        "message": "hello",
        "thread_id": "nonexistent-id"
    })
    assert resp.status_code == 404
