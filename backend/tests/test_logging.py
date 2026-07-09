"""Request-ID propagation and the JSON log formatter."""

import json
import logging

from app.logging_config import JsonFormatter


def test_request_id_header_is_added(client):
    r = client.get("/health")
    assert r.headers.get("X-Request-ID")  # generated when the caller didn't supply one


def test_request_id_is_echoed_when_provided(client):
    r = client.get("/health", headers={"X-Request-ID": "trace-abc-123"})
    assert r.headers["X-Request-ID"] == "trace-abc-123"


def test_json_formatter_emits_structured_line():
    record = logging.LogRecord("nutriscan", logging.INFO, "path", 1, "hello world", None, None)
    record.request_id = "rid-1"
    out = json.loads(JsonFormatter().format(record))
    assert out["message"] == "hello world"
    assert out["request_id"] == "rid-1"
    assert out["level"] == "INFO"
