"""Profile read/update and the targets it drives."""

COMPLETE = {
    "age": 30, "sex": "male", "height_cm": 180,
    "weight_kg": 75, "activity_level": "moderate", "goal": "maintain",
}


def test_update_and_read_profile(auth_client):
    r = auth_client.put("/api/profile", json=COMPLETE)
    assert r.status_code == 200
    assert auth_client.get("/api/profile").json()["age"] == 30


def test_targets_generic_until_profile_complete(auth_client):
    t = auth_client.get("/api/profile/targets")
    assert t.status_code == 200
    assert t.json()["complete"] is False


def test_targets_personalized_when_complete(auth_client):
    auth_client.put("/api/profile", json=COMPLETE)
    t = auth_client.get("/api/profile/targets").json()
    assert t["complete"] is True
    assert t["calories"] == 2682
