"""Contract: Rag_llm (recipe generation + RAG chat) <-> app.

Mirrors the HTTP API documented in the Rag_llm README (`POST /api/v1/generate` and
`POST /api/v1/chat`). The service is stateless: the app sends the whole conversation
history on each chat call. All text is French.
"""

from enum import Enum
from typing import Literal

from pydantic import BaseModel, Field

from contracts.vision import NutritionAnalysis


class Role(str, Enum):
    USER = "user"
    ASSISTANT = "assistant"


class ChatMessage(BaseModel):
    role: Role
    content: str = Field(min_length=1, max_length=4000)


class Source(BaseModel):
    """A recipe from the RAG store that supported an answer."""

    title: str
    url: str | None = None


class Recipe(BaseModel):
    title: str
    cook_time: str | None = None
    used_ingredients: list[str]
    steps: list[str]
    emissions_kgco2eq: float | None = Field(
        default=None, ge=0, description="CodeCarbon estimate for this generation."
    )


class RecipeRequest(BaseModel):
    """Body of `POST /api/v1/generate` ("frigo vide" mode)."""

    ingredients: list[str] = Field(min_length=1, max_length=100)
    dietary_constraints: list[str] = Field(default_factory=list, max_length=20)

    @classmethod
    def from_analysis(
        cls, analysis: NutritionAnalysis, dietary_constraints: list[str] | None = None
    ) -> "RecipeRequest":
        """Build a request from the ingredients detected by vision_engine."""
        names = list(dict.fromkeys(i.name for i in analysis.ingredients))
        return cls(ingredients=names, dietary_constraints=dietary_constraints or [])


class RecipeResponse(BaseModel):
    status: Literal["success"] = "success"
    recipe: Recipe


class ChatRequest(BaseModel):
    """Body of `POST /api/v1/chat`."""

    message: str = Field(min_length=1, max_length=2000)
    history: list[ChatMessage] = Field(
        default_factory=list,
        max_length=50,
        description="Previous turns, oldest first, excluding `message`.",
    )


class ChatData(BaseModel):
    response: str
    sources: list[Source] = Field(min_length=1, description="Answers must be sourced.")
    emissions_kgco2eq: float | None = Field(default=None, ge=0)


class ChatResponse(BaseModel):
    status: Literal["success"] = "success"
    data: ChatData


class ErrorResponse(BaseModel):
    """Body of non-2xx responses (FastAPI's default `detail`; to confirm with Rag_llm)."""

    detail: str
