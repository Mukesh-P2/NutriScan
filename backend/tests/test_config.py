"""Config validation: insecure settings are caught, and prod is stricter than dev."""

from app.config import DEFAULT_JWT_SECRET, Settings


def _good(**over):
    base = dict(jwt_secret="a-strong-random-secret", gemini_api_key="key", cors_origins="https://app.example.com")
    base.update(over)
    return Settings(**base)


def test_is_prod_flag():
    assert Settings(app_env="prod").is_prod is True
    assert Settings(app_env="dev").is_prod is False


def test_good_config_has_no_problems():
    assert _good().validate_for_env() == []


def test_default_secret_is_flagged():
    problems = _good(jwt_secret=DEFAULT_JWT_SECRET).validate_for_env()
    assert any("JWT_SECRET" in p for p in problems)


def test_missing_gemini_key_is_flagged():
    problems = _good(gemini_api_key="").validate_for_env()
    assert any("GEMINI_API_KEY" in p for p in problems)


def test_wildcard_cors_is_flagged():
    problems = _good(cors_origins="*").validate_for_env()
    assert any("CORS" in p for p in problems)
