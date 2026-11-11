"""Conversions between a `NutritionAnalysis` and the rows of the editable ingredient table."""

from contracts import AnalyzeIngredientsRequest, CookingState, IngredientInput, NutritionAnalysis

NAME, STATE, GRAMS = "Ingredient", "Cooking state", "Weight (g)"


def to_rows(analysis: NutritionAnalysis) -> list[dict]:
    """One table row per ingredient, in the units shown to the user."""
    return [
        {NAME: i.name, STATE: i.cooking_state.value, GRAMS: round(i.estimated_grams, 1)}
        for i in analysis.ingredients
    ]


def to_request(rows: list[dict], portions: int) -> AnalyzeIngredientsRequest | None:
    """Build the recompute request. Blank rows are skipped, a missing weight is left to the
    nutrition module to estimate. Returns None when no ingredient is left."""
    ingredients = []
    for row in rows:
        name = row.get(NAME)
        name = name.strip().lower() if isinstance(name, str) else ""
        if not name:
            continue
        grams = row.get(GRAMS)
        state = row.get(STATE) or CookingState.UNKNOWN.value
        ingredients.append(
            IngredientInput(
                name=name,
                grams=grams if grams and grams > 0 else None,
                cooking_state=CookingState(state),
            )
        )
    if not ingredients:
        return None
    return AnalyzeIngredientsRequest(ingredients=ingredients, portions=portions)
