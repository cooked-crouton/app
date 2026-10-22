import pytest
from pydantic import ValidationError

from contracts import (
    AnalyzeIngredientsRequest,
    ChatData,
    ChatRequest,
    ChatResponse,
    CookingState,
    DetectedIngredient,
    IngredientInput,
    Macros,
    NutritionAnalysis,
    RecipeRequest,
    RecipeResponse,
)

MACROS = Macros(calories_kcal=100, protein_g=5, carbs_g=10, fat_g=2)


def _analysis() -> NutritionAnalysis:
    ing = DetectedIngredient(
        name="riz", estimated_grams=150, cooking_state=CookingState.BOILED, macros=MACROS
    )
    return NutritionAnalysis(
        ingredients=[ing], total_macros=MACROS, portions=2, macros_per_portion=MACROS
    )


def test_analysis_roundtrip_json():
    a = _analysis()
    assert NutritionAnalysis.model_validate_json(a.model_dump_json()) == a


def test_cooking_state_defaults_to_unknown():
    ing = DetectedIngredient(name="oeuf", estimated_grams=50, macros=MACROS)
    assert ing.cooking_state is CookingState.UNKNOWN


@pytest.mark.parametrize("grams", [0, -5])
def test_non_positive_grams_rejected(grams):
    with pytest.raises(ValidationError):
        DetectedIngredient(name="oeuf", estimated_grams=grams, macros=MACROS)


def test_negative_macros_rejected():
    with pytest.raises(ValidationError):
        Macros(calories_kcal=-1, protein_g=0, carbs_g=0, fat_g=0)


def test_calories_are_optional():
    m = Macros(protein_g=1, carbs_g=2, fat_g=3)
    assert m.calories_kcal is None


def test_ingredient_only_request():
    req = AnalyzeIngredientsRequest(ingredients=[IngredientInput(name="oeuf")])
    assert req.ingredients[0].grams is None and req.portions == 1
    with pytest.raises(ValidationError):
        AnalyzeIngredientsRequest(ingredients=[])
    with pytest.raises(ValidationError):
        IngredientInput(name="oeuf", grams=0)


def test_recipe_request_matches_rag_llm_example():
    req = RecipeRequest.model_validate(
        {"ingredients": ["œufs", "tomates", "oignon"], "dietary_constraints": ["végétarien"]}
    )
    assert req.model_dump() == {
        "ingredients": ["œufs", "tomates", "oignon"],
        "dietary_constraints": ["végétarien"],
    }
    with pytest.raises(ValidationError):
        RecipeRequest(ingredients=[])


def test_recipe_request_from_analysis_dedupes_names():
    analysis = _analysis()
    analysis.ingredients.append(analysis.ingredients[0])
    req = RecipeRequest.from_analysis(analysis, ["végétarien"])
    assert req.ingredients == ["riz"] and req.dietary_constraints == ["végétarien"]


def test_recipe_response_matches_rag_llm_example():
    resp = RecipeResponse.model_validate(
        {
            "status": "success",
            "recipe": {
                "title": "Poêlée de tomates aux œufs et oignons",
                "cook_time": "15 min",
                "used_ingredients": ["œufs", "tomates", "oignon"],
                "steps": ["Émincer l'oignon."],
                "emissions_kgco2eq": 0.00003851635342786505,
            },
        }
    )
    assert resp.recipe.used_ingredients[0] == "œufs"


def test_chat_request_defaults_and_validation():
    req = ChatRequest(message="Par quoi remplacer le beurre ?")
    assert req.history == []
    with pytest.raises(ValidationError):
        ChatRequest(message="")
    with pytest.raises(ValidationError):
        ChatRequest(message="hi", history=[{"role": "system", "content": "x"}])


def test_size_limits_reject_oversized_input():
    with pytest.raises(ValidationError):
        ChatRequest(message="x" * 2001)
    with pytest.raises(ValidationError):
        ChatRequest(message="hi", history=[{"role": "user", "content": "x"}] * 51)


def test_chat_response_matches_rag_llm_example_and_requires_sources():
    resp = ChatResponse.model_validate(
        {
            "status": "success",
            "data": {
                "response": "Utilisez du fromage blanc 0%.",
                "sources": [{"title": "Carbonara", "url": "https://example.org/r"}],
                "emissions_kgco2eq": 0.00002148102391823901,
            },
        }
    )
    assert resp.data.sources[0].title == "Carbonara"
    with pytest.raises(ValidationError):
        ChatData(response="Utilisez du fromage blanc.", sources=[])
