"""Contract: recipe generation and Q&A module <-> app (PROPOSAL, to be agreed).

The service is stateless: the app sends the whole conversation history on each
chat call. Source fields mirror what the RAG store keeps per recipe
(`url`, `title`).
"""

from enum import Enum

from pydantic import BaseModel, Field

from contracts.vision import NutritionAnalysis


class Role(str, Enum):
    USER = "user"
    ASSISTANT = "assistant"


class ChatMessage(BaseModel):
    role: Role
    content: str = Field(min_length=1)


class Source(BaseModel):
    """A retrieved recipe/document that supported an answer."""

    title: str
    url: str | None = None
    snippet: str | None = Field(default=None, description="Short supporting excerpt.")
    score: float | None = Field(default=None, description="Retrieval similarity score.")


class RecipeIngredient(BaseModel):
    name: str
    quantity: str | None = None
    unit: str | None = None


class Recipe(BaseModel):
    title: str
    servings: int = Field(default=1, ge=1)
    cook_time: str | None = None
    ingredients: list[RecipeIngredient]
    steps: list[str]


class RecipeRequest(BaseModel):
    """Generate a recipe from the ingredients detected in a photo."""

    analysis: NutritionAnalysis
    constraints: list[str] = Field(
        default_factory=list, description="Free-form, e.g. vegetarian, no gluten."
    )
    servings: int = Field(default=1, ge=1)
    max_cook_time_minutes: int | None = Field(default=None, gt=0)


class RecipeResponse(BaseModel):
    recipe: Recipe
    sources: list[Source] = Field(default_factory=list)


class ChatRequest(BaseModel):
    """Ask a question about the current recipe."""

    question: str = Field(min_length=1)
    history: list[ChatMessage] = Field(
        default_factory=list, description="Previous turns, oldest first, excluding `question`."
    )
    recipe: Recipe | None = None
    analysis: NutritionAnalysis | None = None


class ChatResponse(BaseModel):
    answer: str
    sources: list[Source] = Field(default_factory=list)


class ErrorResponse(BaseModel):
    """Body of every non-2xx response (matches FastAPI's `detail`)."""

    detail: str
