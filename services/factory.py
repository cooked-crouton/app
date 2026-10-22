"""Single place deciding which implementation the UI gets (`USE_MOCKS`)."""

from dataclasses import dataclass

from config import Settings
from services.interfaces import ChatService, RecipeService, VisionService
from services.mocks import MockChatService, MockRecipeService, MockVisionService


@dataclass(frozen=True)
class Services:
    vision: VisionService
    recipe: RecipeService
    chat: ChatService


def get_services(settings: Settings) -> Services:
    """Return mock services when `settings.use_mocks`, the real clients otherwise."""
    if settings.use_mocks:
        # Small delays make spinners and streaming visible while developing the UI.
        return Services(
            vision=MockVisionService(delay=1.0),
            recipe=MockRecipeService(delay=0.5),
            chat=MockChatService(delay=0.3),
        )
    raise NotImplementedError(
        "Real services are not implemented yet. Set USE_MOCKS=true in your .env."
    )
