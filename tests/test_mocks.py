import pytest

import config
from contracts import (
    AnalyzeIngredientsRequest,
    ChatRequest,
    CookingState,
    IngredientInput,
    NutritionAnalysis,
    RecipeRequest,
)
from services.factory import get_services
from services.mocks import MockChatService, MockRecipeService, MockVisionService
from utils.streaming import stream_text


def _settings(monkeypatch, use_mocks: str) -> config.Settings:
    monkeypatch.setenv("USE_MOCKS", use_mocks)
    return config.load_settings()


def _assert_consistent(a: NutritionAnalysis) -> None:
    assert a.total_macros.protein_g == pytest.approx(sum(i.macros.protein_g for i in a.ingredients), abs=0.2)
    assert a.total_macros.calories_kcal == pytest.approx(sum(i.macros.calories_kcal for i in a.ingredients), abs=0.2)
    assert a.macros_per_portion.carbs_g == pytest.approx(a.total_macros.carbs_g / a.portions, abs=0.1)


def test_vision_image_returns_fixed_french_plate():
    a = MockVisionService().analyze_image(b"fake-jpeg", portions=2)
    assert [i.name for i in a.ingredients] == ["poulet", "riz", "brocoli"]
    assert a.portions == 2
    _assert_consistent(a)


def test_vision_rejects_empty_image():
    with pytest.raises(ValueError):
        MockVisionService().analyze_image(b"")


def test_vision_ingredients_keeps_given_grams_and_defaults():
    req = AnalyzeIngredientsRequest(
        ingredients=[
            IngredientInput(name="œufs", grams=120, cooking_state=CookingState.FRIED),
            IngredientInput(name="ingrédient inconnu"),
        ]
    )
    a = MockVisionService().analyze_ingredients(req)
    assert [i.estimated_grams for i in a.ingredients] == [120, 100]
    assert a.ingredients[0].cooking_state is CookingState.FRIED
    _assert_consistent(a)


def test_recipe_uses_only_given_ingredients():
    req = RecipeRequest(ingredients=["œufs", "tomates"], dietary_constraints=["végétarien"])
    resp = MockRecipeService().generate(req)
    assert resp.recipe.used_ingredients == ["œufs", "tomates"]
    assert "végétarien" in resp.recipe.title and resp.recipe.steps


def test_chat_answer_is_sourced():
    data = MockChatService().ask(ChatRequest(message="Par quoi remplacer le beurre ?"))
    assert data.response and len(data.sources) >= 1


def test_stream_text_reassembles_exactly():
    text = "Utilisez du fromage blanc 0%."
    chunks = list(stream_text(text, delay=0))
    assert len(chunks) > 1 and "".join(chunks) == text


def test_factory_returns_mocks_when_enabled(monkeypatch):
    services = get_services(_settings(monkeypatch, "true"))
    assert isinstance(services.vision, MockVisionService)
    assert isinstance(services.recipe, MockRecipeService)
    assert isinstance(services.chat, MockChatService)


def test_factory_real_services_not_available_yet(monkeypatch):
    with pytest.raises(NotImplementedError, match="USE_MOCKS"):
        get_services(_settings(monkeypatch, "false"))
