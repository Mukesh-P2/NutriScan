"""AI-backed routes work end-to-end with a monkeypatched Gemini (no real API calls)."""

from app.schemas import AskResponse, FoodSuggestions
from tests.helpers import make_analysis


def test_ask_endpoint_uses_gemini(client, patch_gemini):
    patch_gemini("ask_question", AskResponse(answer="Milk is fine in moderation."))
    r = client.post("/api/ask", data={"question": "is milk healthy?"})
    assert r.status_code == 200
    assert "Milk" in r.json()["answer"]


def test_analyze_endpoint_uses_gemini(client, patch_gemini):
    patch_gemini("analyze_images", make_analysis(product_name="Choco Bar", barcode=None))
    r = client.post("/api/analyze", files={"images": ("label.jpg", b"fakeimagebytes", "image/jpeg")})
    assert r.status_code == 200
    assert r.json()["product_name"] == "Choco Bar"


def test_suggestions_endpoint_uses_gemini(auth_client, patch_gemini):
    patch_gemini("suggest_foods", FoodSuggestions(summary="Add protein.", disclaimer="Not medical advice."))
    r = auth_client.get("/api/consumption/suggestions")
    assert r.status_code == 200
    assert r.json()["summary"] == "Add protein."
