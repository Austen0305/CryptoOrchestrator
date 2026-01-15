import asyncio
from collections.abc import AsyncGenerator, Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from server_fastapi.config.settings import get_settings
from server_fastapi.database.session import get_db_session
from server_fastapi.main import app
from server_fastapi.models.base import Base

settings = get_settings()


@pytest.fixture(scope="session")
def event_loop() -> Generator:
    """Create an instance of the default event loop for each test case."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
async def db_engine():
    # Use SQLite for tests or a test container
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield engine

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

    await engine.dispose()


@pytest.fixture
async def db_session(db_engine) -> AsyncGenerator[AsyncSession, None]:
    async_session = async_sessionmaker(db_engine, expire_on_commit=False)
    async with async_session() as session:
        yield session


@pytest.fixture
async def client(db_session) -> AsyncGenerator[TestClient, None]:
    # Override dependency
    def get_db_override():
        yield db_session

    app.dependency_overrides[get_db_session] = get_db_override

    with TestClient(app) as c:
        yield c

    app.dependency_overrides.clear()
