"""All Gemini API calls live here so routers stay thin."""

from google import genai
from google.genai import types

from app.config import settings
from app.prompts import ANALYZE_INSTRUCTIONS, ASK_INSTRUCTIONS
from app.schemas import AnalysisResult, AskResponse, Verdict

_client: genai.Client | None = None

# Deterministic sampling so the same input yields the same verdict/score across runs.
_TEMPERATURE = 0.0
_SEED = 7


def _get_client() -> genai.Client:
    global _client
    if _client is None:
        if not settings.gemini_api_key:
            raise RuntimeError("GEMINI_API_KEY is not set. Copy .env.example to .env and add your key.")
        _client = genai.Client(api_key=settings.gemini_api_key)
    return _client


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
    score -= find("saturated fat") / 5.0
    score -= find("sodium") / 5.0
    score -= find("sugar") / 5.0

    if result.contains_trans_fat:
        score -= 15
    if result.is_ultra_processed:
        score -= 10
    if result.contains_palm_oil:
        score -= 5
    if result.main_ingredient_refined_grain:
        score -= 5

    if find("fiber", "fibre") >= 15:
        score += 5
    if find("protein") >= 15:
        score += 5
    if not result.has_ingredients:  # whole / minimally-processed food
        score += 10

    final = max(0, min(100, round(score / 5) * 5))
    result.score = final
    result.verdict = Verdict.healthy if final >= 70 else Verdict.moderate if final >= 40 else Verdict.unhealthy


def analyze_images(images: list[tuple[bytes, str]], total_weight: str | None = None) -> AnalysisResult:
    """Analyze one or more images of the same product. `images` is a list of (bytes, mime_type)."""
    client = _get_client()
    parts: list[types.Part] = [types.Part.from_text(text=ANALYZE_INSTRUCTIONS)]
    if total_weight:
        parts.append(types.Part.from_text(text=f"Total pack weight provided by the user: {total_weight}"))
    for data, mime_type in images:
        parts.append(types.Part.from_bytes(data=data, mime_type=mime_type))

    response = client.models.generate_content(
        model=settings.gemini_model,
        contents=parts,
        config=types.GenerateContentConfig(
            temperature=_TEMPERATURE,
            seed=_SEED,
            response_mime_type="application/json",
            response_schema=AnalysisResult,
        ),
    )
    result = AnalysisResult.model_validate_json(response.text)
    _score_from_nutrients(result)  # deterministic score, overrides the model's guess
    return result


def ask_question(question: str, image: tuple[bytes, str] | None = None) -> AskResponse:
    """Answer a free-form food question, optionally with a supporting image."""
    client = _get_client()
    parts: list[types.Part] = [
        types.Part.from_text(text=ASK_INSTRUCTIONS),
        types.Part.from_text(text=f"Question: {question}"),
    ]
    if image is not None:
        data, mime_type = image
        parts.append(types.Part.from_bytes(data=data, mime_type=mime_type))

    response = client.models.generate_content(
        model=settings.gemini_model,
        contents=parts,
        config=types.GenerateContentConfig(
            temperature=_TEMPERATURE,
            seed=_SEED,
            response_mime_type="application/json",
            response_schema=AskResponse,
        ),
    )
    return AskResponse.model_validate_json(response.text)
