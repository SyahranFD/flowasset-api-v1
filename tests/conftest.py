import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession

from app.core.database import Base
from app.core.deps import get_db
from main import app

TEST_DATABASE_URL = "sqlite+aiosqlite:///./test_flowasset.db"

test_engine = create_async_engine(
    TEST_DATABASE_URL,
    echo=False,
    connect_args={"check_same_thread": False},
)

TestSessionLocal = async_sessionmaker(
    bind=test_engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)


@pytest_asyncio.fixture(scope="function", autouse=True)
async def setup_database():
    """Drop and recreate all tables before each test for full isolation."""
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest_asyncio.fixture
async def client(setup_database):
    async def override_get_db():
        async with TestSessionLocal() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise

    app.dependency_overrides[get_db] = override_get_db

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as ac:
        yield ac

    app.dependency_overrides.clear()


@pytest_asyncio.fixture
async def auth_headers(client: AsyncClient) -> dict:
    """Register + login a test user, return Authorization headers."""
    await client.post("/api/v1/auth/register", json={
        "email": "testuser@flowasset.com",
        "password": "testpassword123",
        "full_name": "Test User",
    })
    response = await client.post("/api/v1/auth/login", json={
        "email": "testuser@flowasset.com",
        "password": "testpassword123",
    })
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}
