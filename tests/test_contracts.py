import pytest
from pydantic import ValidationError

from contracts import (
    AnalyzeIngredientsRequest,
    ChatResponse,
    IngredientInput,
    ChatRequest,
    CookingState,
    DetectedIngredient,
    Macros,
    NutritionAnalysis,
    RecipeRequest,
)

MACROS = Macros(calories_kcal=100, protein_g=5, carbs_g=10, fat_g=2)


def _analysis() -> NutritionAnalysis:
    ing = DetectedIngredient(
        name="rice", estimated_grams=150, cooking_state=CookingState.BOILED, macros=MACROS
    )
    return NutritionAnalysis(
        ingredients=[ing], total_macros=MACROS, portions=2, macros_per_portion=MACROS
    )


def test_analysis_roundtrip_json():
    a = _analysis()
    assert NutritionAnalysis.model_validate_json(a.model_dump_json()) == a


def test_cooking_state_defaults_to_unknown():
    ing = DetectedIngredient(name="egg", estimated_grams=50, macros=MACROS)
    assert ing.cooking_state is CookingState.UNKNOWN


@pytest.mark.parametrize("grams", [0, -5])
def test_non_positive_grams_rejected(grams):
    with pytest.raises(ValidationError):
        DetectedIngredient(name="egg", estimated_grams=grams, macros=MACROS)


def test_negative_macros_rejected():
    with pytest.raises(ValidationError):
        Macros(calories_kcal=-1, protein_g=0, carbs_g=0, fat_g=0)


def test_chat_request_defaults_and_validation():
    req = ChatRequest(question="Can I swap the rice?")
    assert req.history == [] and req.recipe is None
    with pytest.raises(ValidationError):
        ChatRequest(question="")
    with pytest.raises(ValidationError):
        ChatRequest(question="hi", history=[{"role": "system", "content": "x"}])


def test_recipe_request_embeds_analysis():
    req = RecipeRequest(analysis=_analysis(), constraints=["vegetarian"])
    assert req.servings == 1 and req.analysis.portions == 2


def test_size_limits_reject_oversized_input():
    with pytest.raises(ValidationError):
        ChatRequest(question="x" * 2001)
    with pytest.raises(ValidationError):
        ChatRequest(question="hi", history=[{"role": "user", "content": "x"}] * 51)


def test_calories_are_optional():
    m = Macros(protein_g=1, carbs_g=2, fat_g=3)
    assert m.calories_kcal is None


def test_ingredient_only_request():
    req = AnalyzeIngredientsRequest(ingredients=[IngredientInput(name="egg")])
    assert req.ingredients[0].grams is None and req.portions == 1
    with pytest.raises(ValidationError):
        AnalyzeIngredientsRequest(ingredients=[])
    with pytest.raises(ValidationError):
        IngredientInput(name="egg", grams=0)


def test_chat_answers_must_be_sourced():
    with pytest.raises(ValidationError):
        ChatResponse(answer="Use applesauce.", sources=[])
    ok = ChatResponse(answer="Use applesauce.", sources=[{"title": "Vegan baking"}])
    assert ok.sources[0].url is None
