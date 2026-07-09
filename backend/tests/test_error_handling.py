"""Global error handling: unexpected errors become a clean 500 with no internal leakage."""

from app.services import gemini


def test_unhandled_exception_returns_clean_500(client_no_raise, monkeypatch):
    def boom(*args, **kwargs):
        raise ValueError("secret internal details that must not leak")

    monkeypatch.setattr(gemini, "ask_question", boom)
    r = client_no_raise.post("/api/ask", data={"question": "is milk healthy?"})

    assert r.status_code == 500
    assert "secret internal details" not in r.text  # no stack trace / internals leaked
    assert r.json()["detail"] == "An unexpected internal error occurred."
    assert r.headers.get("X-Request-ID")  # still traceable


def test_http_exception_shape_unchanged(client):
    # A normal 4xx keeps the standard {"detail": ...} contract the frontend relies on.
    r = client.get("/api/consumption/today")  # no auth
    assert r.status_code == 401
    assert "detail" in r.json()
