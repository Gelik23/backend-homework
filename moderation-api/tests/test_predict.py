import pytest
from fastapi.testclient import TestClient

from main import app, moderation_service

client = TestClient(app)


@pytest.fixture
def advertisement() -> dict[str, int | bool | str]:
    return {
        "seller_id": 12,
        "is_verified_seller": False,
        "item_id": 42,
        "name": "Настольная лампа",
        "description": "Лампа в хорошем состоянии",
        "category": 3,
        "images_qty": 0,
    }


@pytest.mark.parametrize(
    ("is_verified", "images_qty", "expected"),
    [
        (True, 0, False),
        (False, 0, True),
        (False, 1, False),
    ],
)
def test_predict(advertisement, is_verified, images_qty, expected):
    advertisement.update(is_verified_seller=is_verified, images_qty=images_qty)

    response = client.post("/predict", json=advertisement)

    assert response.status_code == 200
    assert response.json() is expected


def test_missing_required_field(advertisement):
    del advertisement["seller_id"]

    response = client.post("/predict", json=advertisement)

    assert response.status_code == 422
    error, = response.json()["detail"]
    assert error["loc"] == ["body", "seller_id"]
    assert error["type"] == "missing"


def test_invalid_field_type(advertisement):
    advertisement["images_qty"] = "0"

    response = client.post("/predict", json=advertisement)

    assert response.status_code == 422
    error, = response.json()["detail"]
    assert error["loc"] == ["body", "images_qty"]
    assert error["type"] == "int_type"


def test_malformed_json():
    response = client.post(
        "/predict", content="{", headers={"Content-Type": "application/json"}
    )

    assert response.status_code == 400
    assert response.json()["detail"][0]["type"] == "json_invalid"


def test_service_error(advertisement, monkeypatch):
    def fail_prediction(_advertisement):
        raise RuntimeError("Unexpected service failure")

    monkeypatch.setattr(moderation_service, "predict_violation", fail_prediction)

    response = client.post("/predict", json=advertisement)

    assert response.status_code == 500
    assert response.json() == {"detail": "Internal server error"}
