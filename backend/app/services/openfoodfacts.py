"""Open Food Facts (OFF) client for barcode + name lookup.

⚠️ Accuracy is the whole point here. OFF is crowd-sourced and GLOBAL: the same barcode may
describe a different country's formulation, and recipes change over time. This module therefore:
  * surfaces provenance (countries the record is tagged for, last-modified date), and
  * attaches explicit `caveats` on every response,
so the product data is presented as a hint to verify — never as authoritative truth. It does
NOT decide anything for the user or overwrite scanned-label data.
"""

from datetime import datetime, timezone

import httpx

from app.lookup_schemas import (
    ProductLookup,
    ProductNutriment,
    ProductSearchResults,
    ProductSummary,
)

_BASE = "https://world.openfoodfacts.org"
# Dedicated full-text search service (the legacy cgi/search.pl frequently 503s under load).
_SEARCH_BASE = "https://search.openfoodfacts.org"
# OFF asks every client to send an identifying User-Agent.
_HEADERS = {"User-Agent": "NutriScan/0.2 (nutrition scanner; contact: nutriscan@example.com)"}
_TIMEOUT = httpx.Timeout(10.0)
_STALE_AFTER_DAYS = 365  # older records get a "may be outdated" caveat

# (display name, OFF nutriment key per 100 g, unit)
_NUTRIMENT_FIELDS = [
    ("Energy", "energy-kcal_100g", "kcal"),
    ("Protein", "proteins_100g", "g"),
    ("Carbohydrate", "carbohydrates_100g", "g"),
    ("Sugars", "sugars_100g", "g"),
    ("Fat", "fat_100g", "g"),
    ("Saturated fat", "saturated-fat_100g", "g"),
    ("Fiber", "fiber_100g", "g"),
    ("Salt", "salt_100g", "g"),
    ("Sodium", "sodium_100g", "g"),
]


class LookupError(Exception):
    """OFF is unreachable or returned an unusable response."""


def _as_text(value) -> str | None:
    """OFF fields come as str OR list depending on endpoint; normalize to a clean string."""
    if isinstance(value, list):
        value = ", ".join(str(v) for v in value if v)
    text = (value or "").strip() if isinstance(value, str) else ""
    return text or None


def _prettify_tags(tags: list[str]) -> list[str]:
    """['en:united-states', 'en:france'] -> ['United States', 'France']."""
    out = []
    for tag in tags:
        label = tag.split(":", 1)[-1].replace("-", " ").strip()
        if label:
            out.append(label.title())
    return out


def _base_caveats() -> list[str]:
    return [
        "Open Food Facts is a crowd-sourced global database. The SAME barcode can have different "
        "ingredients or nutrition in different countries, and recipes change over time.",
        "Always verify this against the actual label on the product you have — treat it as a hint, "
        "not a definitive answer.",
    ]


def _country_caveats(record_countries: list[str], requested: str | None) -> list[str]:
    if not requested:
        return []
    wanted = requested.strip().lower()
    if record_countries and not any(wanted in c.lower() for c in record_countries):
        listed = ", ".join(record_countries) or "unspecified regions"
        return [
            f"⚠️ You asked about “{requested}”, but this record is tagged for {listed}. "
            "The version sold in your country may differ — double-check the label."
        ]
    return []


def _freshness(last_modified_t: int | None) -> tuple[str | None, list[str]]:
    if not last_modified_t:
        return None, []
    dt = datetime.fromtimestamp(last_modified_t, tz=timezone.utc)
    date_str = dt.strftime("%Y-%m-%d")
    age_days = (datetime.now(timezone.utc) - dt).days
    if age_days > _STALE_AFTER_DAYS:
        yrs = age_days // 365
        return date_str, [
            f"This record was last updated {date_str} (~{yrs}+ year(s) ago) and may be outdated."
        ]
    return date_str, []


def _extract_nutriments(nutriments: dict) -> list[ProductNutriment]:
    out = []
    for name, key, unit in _NUTRIMENT_FIELDS:
        value = nutriments.get(key)
        if value is None or value == "":
            continue
        try:
            amount = f"{float(value):g} {unit}"
        except (TypeError, ValueError):
            amount = f"{value} {unit}"
        out.append(ProductNutriment(name=name, amount=amount, per="100 g"))
    return out


def lookup_barcode(barcode: str, country: str | None = None) -> ProductLookup:
    barcode = barcode.strip()
    url = f"{_BASE}/api/v2/product/{barcode}.json"
    try:
        resp = httpx.get(url, headers=_HEADERS, timeout=_TIMEOUT)
        resp.raise_for_status()
        data = resp.json()
    except httpx.HTTPError as exc:
        raise LookupError(f"Could not reach the food database: {exc}") from exc

    if data.get("status") != 1 or not data.get("product"):
        return ProductLookup(
            found=False,
            barcode=barcode,
            caveats=["No product found for this barcode in Open Food Facts. Scan the label instead."],
        )

    p = data["product"]
    countries = _prettify_tags(p.get("countries_tags", []))
    last_modified, fresh_caveats = _freshness(p.get("last_modified_t"))

    return ProductLookup(
        found=True,
        barcode=barcode,
        product_name=_as_text(p.get("product_name")),
        brands=_as_text(p.get("brands")),
        ingredients_text=_as_text(p.get("ingredients_text")),
        allergens=_prettify_tags(p.get("allergens_tags", [])),
        nutriments=_extract_nutriments(p.get("nutriments", {})),
        countries=countries,
        image_url=p.get("image_front_url") or p.get("image_url"),
        last_modified=last_modified,
        source_url=f"{_BASE}/product/{barcode}",
        caveats=_base_caveats() + _country_caveats(countries, country) + fresh_caveats,
    )


def search_products(query: str, country: str | None = None, page_size: int = 10) -> ProductSearchResults:
    query = query.strip()
    # Search-a-licious accepts a Lucene-style query; scope by country tag when given.
    q = query
    if country:
        slug = country.strip().lower().replace(" ", "-")
        q = f'{query} countries_tags:"en:{slug}"'
    params = {
        "q": q,
        "page_size": page_size,
        "fields": "code,product_name,brands,countries_tags,image_front_small_url,image_small_url",
    }

    try:
        resp = httpx.get(f"{_SEARCH_BASE}/search", params=params, headers=_HEADERS, timeout=_TIMEOUT)
        resp.raise_for_status()
        data = resp.json()
    except httpx.HTTPError as exc:
        raise LookupError(f"Could not reach the food database: {exc}") from exc

    results = []
    for p in data.get("hits", []):
        code = (p.get("code") or "").strip()
        if not code:
            continue
        results.append(
            ProductSummary(
                barcode=code,
                product_name=_as_text(p.get("product_name")),
                brands=_as_text(p.get("brands")),
                countries=_prettify_tags(p.get("countries_tags", [])),
                image_url=p.get("image_front_small_url") or p.get("image_small_url"),
            )
        )

    caveats = [
        "Results are from the crowd-sourced Open Food Facts database and may include the wrong "
        "region's version of a product. Pick the match whose brand/country fits what you have, "
        "then confirm against the physical label.",
    ]
    return ProductSearchResults(
        query=query,
        country_filter=country,
        count=len(results),
        results=results,
        caveats=caveats,
    )
