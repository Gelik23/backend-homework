import asyncpg
import pytest
from httpx import ASGITransport, AsyncClient

from database import get_connection
from main import app
from repository import AdvertisementRepository, UserRepository


@pytest.fixture
def anyio_backend():
    return "asyncio"


@pytest.fixture
async def connection():
    connection = await asyncpg.connect(
        host="localhost", port=5435, database="hw",
        user="postgres", password="postgres",
    )
    transaction = connection.transaction()
    await transaction.start()
    try:
        yield connection
    finally:
        await transaction.rollback()
        await connection.close()


@pytest.fixture
async def db_client(connection):
    async def override_connection():
        yield connection

    app.dependency_overrides[get_connection] = override_connection
    try:
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test",
        ) as client:
            yield client
    finally:
        app.dependency_overrides.pop(get_connection, None)


@pytest.fixture
async def seller_id(connection):
    return await UserRepository(connection).create("Анна", "Иванова", False, 0)


@pytest.fixture
async def item_id(connection, seller_id):
    return await AdvertisementRepository(connection).create(
        seller_id, "Лампа", "Рабочая лампа", 3, 0,
    )
