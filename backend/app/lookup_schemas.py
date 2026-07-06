"""Schemas for food-database (Open Food Facts) lookup.

Design note — accuracy & safety: a barcode is NOT a guarantee of a single formulation.
The same GTIN can be sold with different ingredients in different countries, and recipes
change over time. So every lookup carries explicit `caveats` and provenance (`countries`,
`last_modified`, `source`); the client must treat this as a *hint to verify against the
physical label*, never as ground truth. We never silently overwrite scanned label data.
"""

from pydantic import BaseModel, Field


class ProductNutriment(BaseModel):
    name: str
    amount: str = Field(description="Value with unit, e.g. '5.2 g'")
    per: str = Field(default="100 g", description="Basis, e.g. '100 g'")


class ProductSummary(BaseModel):
    """A single search hit — enough to let the user pick the right product/region."""

    barcode: str
    product_name: str | None = None
    brands: str | None = None
    countries: list[str] = Field(default_factory=list, description="Countries this record is tagged for")
    image_url: str | None = None


class ProductSearchResults(BaseModel):
    query: str
    country_filter: str | None = None
    count: int
    results: list[ProductSummary] = Field(default_factory=list)
    caveats: list[str] = Field(default_factory=list)


class ProductLookup(BaseModel):
    """Full detail for one product, with provenance and safety caveats."""

    found: bool
    barcode: str | None = None
    product_name: str | None = None
    brands: str | None = None
    ingredients_text: str | None = None
    allergens: list[str] = Field(default_factory=list)
    nutriments: list[ProductNutriment] = Field(default_factory=list)
    countries: list[str] = Field(default_factory=list, description="Where OFF says this record is sold")
    image_url: str | None = None
    last_modified: str | None = Field(default=None, description="Date the OFF record was last updated (YYYY-MM-DD)")
    source: str = "Open Food Facts"
    source_url: str | None = None
    caveats: list[str] = Field(
        default_factory=list,
        description="Region/freshness warnings — always verify against the physical label",
    )
