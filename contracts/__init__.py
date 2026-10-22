"""Shared Pydantic schemas describing how the app talks to the other modules."""

from contracts.recipe import (
    ChatData,
    ChatMessage,
    ChatRequest,
    ChatResponse,
    ErrorResponse,
    Recipe,
    RecipeRequest,
    RecipeResponse,
    Role,
    Source,
)
from contracts.vision import (
    AnalyzeIngredientsRequest,
    CookingState,
    DetectedIngredient,
    IngredientInput,
    Macros,
    NutritionAnalysis,
    VisionEngine,
)

__all__ = [
    "AnalyzeIngredientsRequest",
    "ChatData",
    "ChatMessage",
    "ChatRequest",
    "ChatResponse",
    "CookingState",
    "DetectedIngredient",
    "ErrorResponse",
    "IngredientInput",
    "Macros",
    "NutritionAnalysis",
    "Recipe",
    "RecipeRequest",
    "RecipeResponse",
    "Role",
    "Source",
    "VisionEngine",
]
