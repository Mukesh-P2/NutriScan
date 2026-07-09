"""Consumption tracking endpoints: preview (no persist), log, today, history, weekly, undo."""

NUTRITION = {
    "calories": 250, "protein_g": 10, "carbs_g": 30, "fat_g": 9,
    "saturated_fat_g": 4, "sugar_g": 12, "fiber_g": 3, "sodium_mg": 300,
}


def _payload(**over):
    p = {"product_name": "Biscuit", "servings": 2, "nutrition": NUTRITION, "product_verdict": "moderate"}
    p.update(over)
    return p


def test_log_then_today_reflects_entry(auth_client):
    auth_client.post("/api/consumption/log", json=_payload())
    today = auth_client.get("/api/consumption/today").json()
    assert len(today["entries"]) == 1
    assert today["calories_consumed"] == 500  # 250 kcal * 2 servings


def test_preview_does_not_persist(auth_client):
    r = auth_client.post("/api/consumption/preview", json=_payload())
    assert r.status_code == 200
    assert auth_client.get("/api/consumption/today").json()["entries"] == []


def test_delete_entry_undoes(auth_client):
    day = auth_client.post("/api/consumption/log", json=_payload()).json()
    entry_id = day["entries"][0]["id"]
    after = auth_client.delete(f"/api/consumption/{entry_id}").json()
    assert after["entries"] == []


def test_history_and_weekly(auth_client):
    auth_client.post("/api/consumption/log", json=_payload())
    assert auth_client.get("/api/consumption/history").status_code == 200
    assert auth_client.get("/api/consumption/weekly").json()["days"] == 7
