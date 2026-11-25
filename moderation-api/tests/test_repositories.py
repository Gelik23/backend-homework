import asyncpg
import pytest

from repository import AdvertisementRepository, UserRepository

pytestmark = pytest.mark.anyio


async def test_create_user(connection):
    user_id = await UserRepository(connection).create("Анна", "О'Нил", True, 2)
    row = await connection.fetchrow("SELECT * FROM users WHERE id = $1", user_id)
    assert dict(row) == {
        "id": user_id, "first_name": "Анна", "last_name": "О'Нил",
        "is_verified": True, "violations_qty": 2,
    }


async def test_create_advertisement(connection, seller_id):
    item_id = await AdvertisementRepository(connection).create(seller_id, "Лампа 'новая'", "", 3, 0)
    row = await connection.fetchrow("SELECT * FROM advertisements WHERE id = $1", item_id)
    assert dict(row) == {
        "id": item_id, "seller_id": seller_id, "name": "Лампа 'новая'",
        "description": "", "category": 3, "images_qty": 0,
    }
    advertisement = await AdvertisementRepository(connection).get_for_prediction(item_id)
    assert advertisement.model_dump() == {
        "item_id": item_id, "seller_id": seller_id, "is_verified_seller": False,
        "name": "Лампа 'новая'", "description": "", "category": 3, "images_qty": 0,
    }


async def test_advertisement_requires_existing_user(connection):
    missing_id = await connection.fetchval("SELECT COALESCE(MAX(id), 0) + 1 FROM users")
    with pytest.raises(asyncpg.ForeignKeyViolationError):
        async with connection.transaction():
            await AdvertisementRepository(connection).create(missing_id, "Лампа", "", 3, 0)


@pytest.mark.parametrize("table", ["users", "advertisements"])
async def test_negative_quantity(connection, seller_id, table):
    with pytest.raises(asyncpg.CheckViolationError):
        async with connection.transaction():
            if table == "users":
                await UserRepository(connection).create("Анна", "Иванова", False, -1)
            else:
                await AdvertisementRepository(connection).create(seller_id, "Лампа", "", 3, -1)


async def test_nonexistent_advertisement(connection):
    missing_id = await connection.fetchval("SELECT COALESCE(MAX(id), 0) + 1 FROM advertisements")
    assert await AdvertisementRepository(connection).get_for_prediction(missing_id) is None
