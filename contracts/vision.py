"""Contract: vision/nutrition module (vision_engine) <-> app (PROPOSAL, to be agreed with the owner).

vision_engine is consumed as a Python module (see `VisionEngine`). It accepts either a photo or a
plain ingredient list and returns the ingredients with estimated weights, cooking state
and macros. Nutrition reference data must be a local copy (e.g. Ciqual), never a
network API.
"""

from enum import Enum
from typing import Protocol

from pydantic import BaseModel, Field


class CookingState(str, Enum):
    """Raw / cooked, and the cooking type when it can be told."""

    RAW = "raw"
    COOKED = "cooked"  # cooked, type unknown
    BOILED = "boiled"
    STEAMED = "steamed"
    FRIED = "fried"
    GRILLED = "grilled"
    ROASTED = "roasted"
    BAKED = "baked"
    UNKNOWN = "unknown"


class Macros(BaseModel):
    """Nutritional values. Energy in kcal, everything else in grams."""

    protein_g: float = Field(ge=0)
    carbs_g: float = Field(ge=0)
    fat_g: float = Field(ge=0)
    calories_kcal: float | None = Field(default=None, ge=0)
    fiber_g: float | None = Field(default=None, ge=0)


class DetectedIngredient(BaseModel):
    name: str = Field(min_length=1, description="Ingredient name, lowercase English.")
    estimated_grams: float = Field(gt=0, description="Estimated or user-given weight.")
    cooking_state: CookingState = CookingState.UNKNOWN
    confidence: float | None = Field(default=None, ge=0, le=1)
    macros: Macros = Field(description="Macros for `estimated_grams` of this ingredient.")


class NutritionAnalysis(BaseModel):
    """Output of the vision/nutrition module."""

    ingredients: list[DetectedIngredient] = Field(max_length=100)
    total_macros: Macros = Field(description="Sum over all ingredients.")
    portions: int = Field(default=1, ge=1, description="Number of portions assumed.")
    macros_per_portion: Macros = Field(description="`total_macros` / `portions`.")


class IngredientInput(BaseModel):
    """One entry of a text-only request. Missing grams are estimated by the module."""

    name: str = Field(min_length=1, max_length=100)
    grams: float | None = Field(default=None, gt=0)
    cooking_state: CookingState = CookingState.UNKNOWN


class AnalyzeIngredientsRequest(BaseModel):
    """Text-only input (no photo)."""

    ingredients: list[IngredientInput] = Field(min_length=1, max_length=100)
    portions: int = Field(default=1, ge=1)


class VisionEngine(Protocol):
    """Interface the app expects from vision_engine (call from a worker thread: inference is slow)."""

    def analyze_image(self, image: bytes, portions: int = 1) -> NutritionAnalysis:
        """Analyze a photo (JPEG/PNG bytes) of ingredients or a dish."""
        ...

    def analyze_ingredients(self, request: AnalyzeIngredientsRequest) -> NutritionAnalysis:
        """Compute grams (when missing) and macros for a given ingredient list."""
        ...
