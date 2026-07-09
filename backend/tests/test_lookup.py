"""Open Food Facts lookup — mocked httpx so no live network is hit."""

import pytest

from app.services import openfoodfacts


class FakeResp:
    def __init__(self, data):
        self._data = data

    def raise_for_status(self):
        pass

    def json(self):
        return self._data


@pytest.fixture(autouse=True)
def clear_off_cache():
    openfoodfacts._cache.clear()
    yield
    openfoodfacts._cache.clear()


def test_barcode_found(client, monkeypatch):
    data = {
        "status": 1,
        "product": {
            "product_name": "Nutella",
            "brands": "Ferrero",
            "nutriments": {"energy-kcal_100g": 539, "sugars_100g": 56.3},
            "countries_tags": ["en:france"],
            "last_modified_t": 1600000000,
        },
    }
    monkeypatch.setattr(openfoodfacts.httpx, "get", lambda *a, **k: FakeResp(data))
    body = client.get("/api/lookup/barcode/3017620422003").json()
    assert body["found"] is True
    assert body["product_name"] == "Nutella"
    assert body["caveats"]  # always caveat-first


def test_barcode_not_found(client, monkeypatch):
    monkeypatch.setattr(openfoodfacts.httpx, "get", lambda *a, **k: FakeResp({"status": 0}))
    r = client.get("/api/lookup/barcode/0000000000000")
    assert r.status_code == 200
    assert r.json()["found"] is False


def test_non_numeric_barcode_rejected(client):
    assert client.get("/api/lookup/barcode/abc").status_code == 400


def test_search_returns_hits(client, monkeypatch):
    data = {"hits": [{"code": "111", "product_name": "Oat Milk", "brands": "Oatly", "countries_tags": ["en:united-kingdom"]}]}
    monkeypatch.setattr(openfoodfacts.httpx, "get", lambda *a, **k: FakeResp(data))
    r = client.get("/api/lookup/search", params={"q": "oat milk"})
    assert r.status_code == 200
    assert r.json()["count"] == 1
