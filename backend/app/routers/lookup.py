"""Food-database lookup endpoints (Open Food Facts).

Public (no auth) — enrichment only. Every response includes caveats about region/freshness;
see app/services/openfoodfacts.py for the accuracy rationale.
"""

from fastapi import APIRouter, HTTPException, Query

from app.lookup_schemas import ProductLookup, ProductSearchResults
from app.services import openfoodfacts

router = APIRouter(prefix="/api/lookup", tags=["lookup"])


@router.get("/barcode/{barcode}", response_model=ProductLookup)
def lookup_barcode(
    barcode: str,
    country: str | None = Query(None, description="Optional country to sanity-check the record against"),
) -> ProductLookup:
    if not barcode.strip().isdigit():
        raise HTTPException(status_code=400, detail="Barcode must be numeric.")
    try:
        return openfoodfacts.lookup_barcode(barcode, country=country)
    except openfoodfacts.LookupError as exc:
        raise HTTPException(status_code=502, detail=str(exc))


@router.get("/search", response_model=ProductSearchResults)
def search_products(
    q: str = Query(..., min_length=2, max_length=100, description="Product name to search"),
    country: str | None = Query(None, description="Optional country filter for regional formulations"),
) -> ProductSearchResults:
    try:
        return openfoodfacts.search_products(q, country=country)
    except openfoodfacts.LookupError as exc:
        raise HTTPException(status_code=502, detail=str(exc))
