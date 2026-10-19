"""Contract: vision/nutrition module -> app (PROPOSAL, to be agreed with the owner).

Flow: the app sends one image; the module returns the detected ingredients with
estimated weights, cooking state and macros.
"""

from enum import Enum

from pydantic import BaseModel, Field


class CookingState(str, Enum):
    RAW = "raw"
    BOILED = "boiled"
    STEAMED = "steamed"
    FRIED = "fried"
    GRILLED = "grilled"
    ROASTED = "roasted"
    BAKED = "baked"
    UNKNOWN = "unknown"


class Macros(BaseModel):
    """Nutritional values. Units are fixed: kcal for energy, grams for the rest."""

    calories_kcal: float = Field(ge=0)
    protein_g: float = Field(ge=0)
    carbs_g: float = Field(ge=0)
    fat_g: float = Field(ge=0)
    fiber_g: float | None = Field(default=None, ge=0)


class DetectedIngredient(BaseModel):
    name: str = Field(min_length=1, description="Ingredient name, lowercase English.")
    estimated_grams: float = Field(gt=0, description="Estimated weight on the plate.")
    cooking_state: CookingState = CookingState.UNKNOWN
    confidence: float | None = Field(default=None, ge=0, le=1)
    macros: Macros = Field(description="Macros for `estimated_grams` of this ingredient.")


class NutritionAnalysis(BaseModel):
    """Response of the vision/nutrition module."""

    ingredients: list[DetectedIngredient] = Field(max_length=100)
    total_macros: Macros = Field(description="Sum over all ingredients.")
    portions: int = Field(default=1, ge=1, description="Number of portions assumed.")
    macros_per_portion: Macros = Field(description="`total_macros` / `portions`.")


class AnalyzeImageRequest(BaseModel):
    """Metadata sent with the image (the image itself is a multipart file part)."""

    portions: int = Field(default=1, ge=1)
