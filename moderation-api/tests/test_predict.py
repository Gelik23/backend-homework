import pytest
from fastapi.testclient import TestClient

from main import app
from routers.predict import moderation_service

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


@pytest.mark.parametrize(
    "field",
    [
        "seller_id",
        "is_verified_seller",
        "item_id",
        "name",
        "description",
        "category",
        "images_qty",
    ],
)
def test_missing_required_field(advertisement, field):
    del advertisement[field]

    response = client.post("/predict", json=advertisement)

    assert response.status_code == 400
    error, = response.json()["detail"]
    assert error["loc"] == ["body", field]
    assert error["type"] == "missing"


@pytest.mark.parametrize(
    ("field", "value", "error_type"),
    [
        ("seller_id", "12", "int_type"),
        ("is_verified_seller", "false", "bool_type"),
        ("item_id", True, "int_type"),
        ("name", 123, "string_type"),
        ("description", [], "string_type"),
        ("category", 1.5, "int_type"),
        ("images_qty", "0", "int_type"),
    ],
)
def test_invalid_field_type(advertisement, field, value, error_type):
    advertisement[field] = value

    response = client.post("/predict", json=advertisement)

    assert response.status_code == 400
    error, = response.json()["detail"]
    assert error["loc"] == ["body", field]
    assert error["type"] == error_type


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


def test_negative_images_qty(advertisement):
    advertisement["images_qty"] = -1

    response = client.post("/predict", json=advertisement)

    assert response.status_code == 400
    error, = response.json()["detail"]
    assert error["loc"] == ["body", "images_qty"]
    assert error["type"] == "greater_than_equal"


def test_missing_body():
    response = client.post("/predict")

    assert response.status_code == 400
    assert response.json()["detail"][0]["type"] == "missing"
