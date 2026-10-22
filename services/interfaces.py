"""Service interfaces the UI depends on. Mocks and real clients both implement them."""

from typing import Protocol

from contracts import ChatData, ChatRequest, RecipeRequest, RecipeResponse, VisionEngine

# vision_engine is consumed as a Python module (see docs/integration.md).
VisionService = VisionEngine


class RecipeService(Protocol):
    """Recipe generation ("frigo vide"), backed by Rag_llm `POST /api/v1/generate`."""

    def generate(self, request: RecipeRequest) -> RecipeResponse: ...


class ChatService(Protocol):
    """RAG chat, backed by Rag_llm `POST /api/v1/chat`.

    Returns the complete answer. Rag_llm does not stream, so progressive display is done
    client-side with `utils.streaming.stream_text`, identically for mocks and real calls.
    """

    def ask(self, request: ChatRequest) -> ChatData: ...
