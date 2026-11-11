"""Small helpers to present a `NutritionAnalysis`."""

from contracts import Macros, NutritionAnalysis


def per_portion(total: Macros, portions: int) -> Macros:
    """`total` divided by the number of portions (calories stay None when unknown)."""
    kcal = total.calories_kcal
    return Macros(
        protein_g=round(total.protein_g / portions, 1),
        carbs_g=round(total.carbs_g / portions, 1),
        fat_g=round(total.fat_g / portions, 1),
        calories_kcal=None if kcal is None else round(kcal / portions, 1),
    )


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
