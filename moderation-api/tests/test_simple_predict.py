from unittest.mock import AsyncMock

import pytest

from repository import AdvertisementRepository
from routers.predict import moderation_service
from service import AdvertisementNotFoundError, SimplePredictionService

pytestmark = pytest.mark.anyio


@pytest.mark.parametrize(
    ("verified", "images_qty", "expected"),
    [(False, 0, True), (False, 1, False), (True, 0, False), (True, 1, False)],
)
async def test_simple_predict(db_client, connection, seller_id, item_id, verified, images_qty, expected):
    await connection.execute("UPDATE users SET is_verified = $1 WHERE id = $2", verified, seller_id)
    await connection.execute("UPDATE advertisements SET images_qty = $1 WHERE id = $2", images_qty, item_id)

    response = await db_client.post("/simple_predict", params={"item_id": item_id})

    assert response.status_code == 200
    assert response.json() is expected
    advertisement = await AdvertisementRepository(connection).get_for_prediction(item_id)
    full_response = await db_client.post("/predict", json=advertisement.model_dump())
    assert full_response.status_code == 200
    assert full_response.json() is expected


@pytest.mark.parametrize("value", [None, "", "abc", "true", "null", "1.5", "1.0", "1e2", "[]", "{}", "0", "-1", "2147483648"])
async def test_invalid_item_id(db_client, value):
    params = {} if value is None else {"item_id": value}
    response = await db_client.post("/simple_predict", params=params)
    assert response.status_code == 400
    error, = response.json()["detail"]
    assert error["loc"] == ["query", "item_id"]
    assert error["msg"]
    if value is None:
        assert error["type"] == "missing"
    else:
        assert error["type"] != "missing"


async def test_json_body_does_not_replace_query(db_client):
    response = await db_client.post("/simple_predict", json={"item_id": 1})
    assert response.status_code == 400
    assert response.json()["detail"][0]["type"] == "missing"


@pytest.mark.parametrize("item_id", [1, 2147483647])
async def test_missing_advertisement(db_client, connection, item_id):
    # Отсутствие записи проверяется и на непустой пользовательской БД.
    async with connection.transaction():
        await connection.execute("DELETE FROM advertisements WHERE id = $1", item_id)
        response = await db_client.post("/simple_predict", params={"item_id": item_id})
    assert response.status_code == 404
    assert response.json() == {"detail": "Advertisement not found"}


async def test_prediction_error(db_client, item_id, monkeypatch):
    def fail(_advertisement):
        raise RuntimeError("Private failure details")
    monkeypatch.setattr(moderation_service, "predict_violation", fail)
    response = await db_client.post("/simple_predict", params={"item_id": item_id})
    assert response.status_code == 500
    assert response.json() == {"detail": "Internal server error"}


async def test_database_query_error(db_client, monkeypatch):
    monkeypatch.setattr(AdvertisementRepository, "get_for_prediction", AsyncMock(side_effect=RuntimeError("SQL failure")))
    response = await db_client.post("/simple_predict", params={"item_id": 1})
    assert response.status_code == 500
    assert response.json() == {"detail": "Internal server error"}


async def test_single_join_query():
    connection = AsyncMock()
    connection.fetchrow.return_value = {
        "item_id": 42, "seller_id": 12, "is_verified_seller": False,
        "name": "Лампа", "description": "Лампа", "category": 3, "images_qty": 0,
    }
    result = await SimplePredictionService(AdvertisementRepository(connection), moderation_service).predict_violation(42)
    assert result is True
    connection.fetchrow.assert_awaited_once()
    query, value = connection.fetchrow.call_args.args
    assert "JOIN users" in query
    assert "WHERE a.id = $1" in query
    assert value == 42
    connection.fetch.assert_not_called()
    connection.fetchval.assert_not_called()


async def test_missing_advertisement_service():
    repository = AsyncMock()
    repository.get_for_prediction.return_value = None
    with pytest.raises(AdvertisementNotFoundError):
        await SimplePredictionService(repository, moderation_service).predict_violation(42)
