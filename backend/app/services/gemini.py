"""All Gemini API calls live here so routers stay thin."""

import time

from google import genai
from google.genai import errors, types
from pydantic import BaseModel

from app.config import settings
from app.prompts import ANALYZE_INSTRUCTIONS, ASK_INSTRUCTIONS, TARGET_GUIDANCE_INSTRUCTIONS
from app.schemas import AnalysisResult, AskResponse, TargetGuidance, Verdict

_client: genai.Client | None = None

# Deterministic sampling so the same input yields the same verdict/score across runs.
_TEMPERATURE = 0.0
_SEED = 7

# Transient errors worth retrying: rate limit (429) and server-side overload (5xx).
_RETRYABLE_CODES = {429, 500, 502, 503, 504}
_MAX_ATTEMPTS = 4
_BASE_DELAY = 2.0  # seconds; exponential backoff: 2s, 4s, 8s


class AIServiceError(Exception):
    """A user-facing AI failure carrying an HTTP status code for the router."""

    def __init__(self, message: str, status_code: int = 502) -> None:
        super().__init__(message)
        self.status_code = status_code


def _get_client() -> genai.Client:
    global _client
    if _client is None:
        if not settings.gemini_api_key:
            raise RuntimeError("GEMINI_API_KEY is not set. Copy .env.example to .env and add your key.")
        _client = genai.Client(api_key=settings.gemini_api_key)
    return _client


def _to_user_error(exc: errors.APIError) -> AIServiceError:
    code = getattr(exc, "code", None)
    if code == 429:
        return AIServiceError("AI rate limit reached. Please wait a minute and try again.", 429)
    if code in _RETRYABLE_CODES:
        return AIServiceError("The AI service is busy right now. Please try again in a moment.", 503)
    return AIServiceError(f"AI request failed: {exc}", 502)


def _generate(parts: list[types.Part], schema: type[BaseModel]):
    """Call Gemini with deterministic config.

    Failover strategy: within each round, try every model in the chain in order (instant
    switch on a transient error). If the whole chain is exhausted, back off and retry the
    chain, up to _MAX_ATTEMPTS rounds. Non-transient errors (e.g. bad request) fail fast.
    """
    client = _get_client()
    config = types.GenerateContentConfig(
        temperature=_TEMPERATURE,
        seed=_SEED,
        response_mime_type="application/json",
        response_schema=schema,
    )
    chain = settings.model_chain
    last_exc: errors.APIError | None = None
    for attempt in range(_MAX_ATTEMPTS):
        for model in chain:
            try:
                return client.models.generate_content(model=model, contents=parts, config=config)
            except errors.APIError as exc:
                if getattr(exc, "code", None) not in _RETRYABLE_CODES:
                    raise _to_user_error(exc) from exc
                last_exc = exc  # transient -> try the next model in the chain immediately
        if attempt < _MAX_ATTEMPTS - 1:
            time.sleep(_BASE_DELAY * (2**attempt))  # whole chain failed this round; back off
    raise _to_user_error(last_exc)  # pragma: no cover - loop always returns or raises


# ---------------------------------------------------------------------------
# Scoring rubric — every weight is tunable here in one place.
# ---------------------------------------------------------------------------
# Points deducted per 1% of daily value, for "limit" (over-consumed) nutrients.
_PENALTY_PER_PCT = {"saturated fat": 0.35, "sodium": 0.25, "sugar": 0.25, "total fat": 0.10}
# Nutrients that also get flat penalties when they're "high" per serving.
# (Total Fat is excluded to avoid double-counting with Saturated Fat.)
_TIERED_NUTRIENTS = {"saturated fat", "sodium", "sugar"}
_HIGH_DV_THRESHOLD, _HIGH_DV_PENALTY = 20, 6  # FDA: >=20% DV per serving = "high"
_VERY_HIGH_DV_THRESHOLD, _VERY_HIGH_DV_PENALTY = 40, 6  # additional on top of "high"
# Flat penalties for processing / ingredient red flags.
_FLAG_PENALTIES = {"trans_fat": 25, "ultra_processed": 15, "palm_oil": 8, "refined_grain": 8}
# Bonuses.
_GOOD_SOURCE_DV = 15  # >=15% DV counts as a good source
_FIBER_BONUS, _PROTEIN_BONUS, _WHOLE_FOOD_BONUS = 5, 8, 15
# Verdict bands.
_HEALTHY_MIN, _MODERATE_MIN = 70, 40


def _score_from_nutrients(result: AnalysisResult) -> None:
    """Compute score & verdict deterministically in Python from the read nutrients.

    Same nutrient numbers in -> exact same score out, regardless of model variance.
    Mutates `result` in place.
    """
    pct: dict[str, int] = {n.name.lower(): n.percent_of_daily for n in result.key_nutrients}

    def find(*keywords: str) -> int:
        for kw in keywords:
            for name, value in pct.items():
                if kw in name:
                    return value
        return 0

    score = 100.0

    for key, per_pct in _PENALTY_PER_PCT.items():
        # Natural sugars in a whole food (e.g. fruit) are not penalized like added sugars.
        if key == "sugar" and not result.has_ingredients:
            continue
        dv = find(key)
        score -= dv * per_pct
        if key in _TIERED_NUTRIENTS:
            if dv >= _HIGH_DV_THRESHOLD:
                score -= _HIGH_DV_PENALTY
            if dv >= _VERY_HIGH_DV_THRESHOLD:
                score -= _VERY_HIGH_DV_PENALTY

    if result.contains_trans_fat:
        score -= _FLAG_PENALTIES["trans_fat"]
    if result.is_ultra_processed:
        score -= _FLAG_PENALTIES["ultra_processed"]
    if result.contains_palm_oil:
        score -= _FLAG_PENALTIES["palm_oil"]
    if result.main_ingredient_refined_grain:
        score -= _FLAG_PENALTIES["refined_grain"]

    if find("fiber", "fibre") >= _GOOD_SOURCE_DV:
        score += _FIBER_BONUS
    if find("protein") >= _GOOD_SOURCE_DV:
        score += _PROTEIN_BONUS
    if not result.has_ingredients:  # whole / minimally-processed food
        score += _WHOLE_FOOD_BONUS

    final = max(0, min(100, round(score / 5) * 5))
    result.score = final
    result.verdict = (
        Verdict.healthy if final >= _HEALTHY_MIN
        else Verdict.moderate if final >= _MODERATE_MIN
        else Verdict.unhealthy
    )


def analyze_images(
    images: list[tuple[bytes, str]],
    total_weight: str | None = None,
    personal_context: str | None = None,
) -> AnalysisResult:
    """Analyze one or more images of the same product. `images` is a list of (bytes, mime_type)."""
    parts: list[types.Part] = [types.Part.from_text(text=ANALYZE_INSTRUCTIONS)]
    if personal_context:
        parts.append(types.Part.from_text(text=personal_context))
    if total_weight:
        parts.append(types.Part.from_text(text=f"Total pack weight provided by the user: {total_weight}"))
    for data, mime_type in images:
        parts.append(types.Part.from_bytes(data=data, mime_type=mime_type))

    response = _generate(parts, AnalysisResult)
    result = AnalysisResult.model_validate_json(response.text)
    _score_from_nutrients(result)  # deterministic score, overrides the model's guess
    return result


def ask_question(
    question: str,
    image: tuple[bytes, str] | None = None,
    personal_context: str | None = None,
) -> AskResponse:
    """Answer a free-form food question, optionally with a supporting image."""
    parts: list[types.Part] = [types.Part.from_text(text=ASK_INSTRUCTIONS)]
    if personal_context:
        parts.append(types.Part.from_text(text=personal_context))
    parts.append(types.Part.from_text(text=f"Question: {question}"))
    if image is not None:
        data, mime_type = image
        parts.append(types.Part.from_bytes(data=data, mime_type=mime_type))

    response = _generate(parts, AskResponse)
    return AskResponse.model_validate_json(response.text)


def target_guidance(facts: str) -> TargetGuidance:
    """Advise around ALREADY-COMPUTED targets. `facts` carries the fixed numbers verbatim;
    the model must not recalculate them (see TARGET_GUIDANCE_INSTRUCTIONS)."""
    parts: list[types.Part] = [
        types.Part.from_text(text=TARGET_GUIDANCE_INSTRUCTIONS),
        types.Part.from_text(text=facts),
    ]
    response = _generate(parts, TargetGuidance)
    return TargetGuidance.model_validate_json(response.text)
