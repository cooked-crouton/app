"""Shared Pydantic schemas describing how the app talks to the other modules."""

from contracts.recipe import (
    ChatMessage,
    ChatRequest,
    ChatResponse,
    ErrorResponse,
    Recipe,
    RecipeIngredient,
    RecipeRequest,
    RecipeResponse,
    Role,
    Source,
)
from contracts.vision import (
    AnalyzeImageRequest,
    CookingState,
    DetectedIngredient,
    Macros,
    NutritionAnalysis,
)

__all__ = [
    "AnalyzeImageRequest",
    "ChatMessage",
    "ChatRequest",
    "ChatResponse",
    "CookingState",
    "DetectedIngredient",
    "ErrorResponse",
    "Macros",
    "NutritionAnalysis",
    "Recipe",
    "RecipeIngredient",
    "RecipeRequest",
    "RecipeResponse",
    "Role",
    "Source",
]
