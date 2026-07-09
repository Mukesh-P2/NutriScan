"""The deterministic scoring rubric — the health-critical number the AI never originates."""

from app.schemas import Verdict
from app.services.gemini import _score_from_nutrients
from tests.helpers import make_analysis, make_nutrient


def test_whole_food_scores_healthy():
    r = make_analysis(
        has_ingredients=False,
        key_nutrients=[make_nutrient("Fiber", 25), make_nutrient("Protein", 20)],
    )
    _score_from_nutrients(r)
    assert r.verdict == Verdict.healthy
    assert r.score >= 70


def test_junk_food_scores_unhealthy():
    r = make_analysis(
        has_ingredients=True,
        is_ultra_processed=True,
        key_nutrients=[
            make_nutrient("Saturated fat", 50),
            make_nutrient("Sugar", 50),
            make_nutrient("Sodium", 45),
        ],
    )
    _score_from_nutrients(r)
    assert r.verdict == Verdict.unhealthy
    assert r.score <= 40


def test_trans_fat_lowers_score():
    kn = [make_nutrient("Sugar", 10)]
    base = make_analysis(has_ingredients=True, key_nutrients=list(kn))
    trans = make_analysis(has_ingredients=True, contains_trans_fat=True, key_nutrients=list(kn))
    _score_from_nutrients(base)
    _score_from_nutrients(trans)
    assert trans.score < base.score


def test_natural_sugar_not_penalized_like_added_sugar():
    whole = make_analysis(has_ingredients=False, key_nutrients=[make_nutrient("Sugar", 40)])
    processed = make_analysis(has_ingredients=True, key_nutrients=[make_nutrient("Sugar", 40)])
    _score_from_nutrients(whole)
    _score_from_nutrients(processed)
    assert whole.score > processed.score
