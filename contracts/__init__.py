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
    "RecipeIngredient",
    "RecipeRequest",
    "RecipeResponse",
    "Role",
    "Source",
    "VisionEngine",
]
