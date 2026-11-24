"""Small helpers to present a `NutritionAnalysis`."""

from contracts import Macros, NutritionAnalysis, Recipe


def per_portion(total: Macros, portions: int) -> Macros:
    """`total` divided by the number of portions (calories stay None when unknown)."""
    kcal = total.calories_kcal
    return Macros(
        protein_g=round(total.protein_g / portions, 1),
        carbs_g=round(total.carbs_g / portions, 1),
        fat_g=round(total.fat_g / portions, 1),
        calories_kcal=None if kcal is None else round(kcal / portions, 1),
    )


def macro_rows(macros: Macros) -> list[dict]:
    """One row per macro for the pie chart; empty when every macro is 0 (nothing to draw)."""
    rows = [
        {"Macro": "Proteins", "Grams": macros.protein_g},
        {"Macro": "Carbs", "Grams": macros.carbs_g},
        {"Macro": "Fats", "Grams": macros.fat_g},
    ]
    return rows if any(r["Grams"] > 0 for r in rows) else []


def ingredient_rows(analysis: NutritionAnalysis) -> list[dict]:
    """What each ingredient brings (for its whole weight), for the contribution table."""
    return [
        {
            "Ingredient": i.name.capitalize(),
            "Weight (g)": round(i.estimated_grams),
            "Calories (kcal)": i.macros.calories_kcal,
            "Proteins (g)": i.macros.protein_g,
            "Carbs (g)": i.macros.carbs_g,
            "Fats (g)": i.macros.fat_g,
        }
        for i in analysis.ingredients
    ]


def recipe_ingredient_lines(recipe: Recipe, analysis: NutritionAnalysis) -> list[str]:
    """`used_ingredients` with the weight from the analysis when known (Rag_llm gives names only)."""
    grams = {i.name.lower(): i.estimated_grams for i in analysis.ingredients}
    lines = []
    for name in recipe.used_ingredients:
        weight = grams.get(name.lower())
        lines.append(name.capitalize() if weight is None else f"{name.capitalize()} : {weight:.0f} g")
    return lines
