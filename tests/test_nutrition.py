from contracts import Macros, Recipe
from services.mocks import MockVisionService
from utils.nutrition import ingredient_rows, macro_rows, per_portion, recipe_ingredient_lines


def test_per_portion_divides_every_value():
    total = Macros(protein_g=40, carbs_g=60, fat_g=20, calories_kcal=600)
    assert per_portion(total, 4) == Macros(protein_g=10, carbs_g=15, fat_g=5, calories_kcal=150)


def test_per_portion_keeps_unknown_calories_unknown():
    assert per_portion(Macros(protein_g=1, carbs_g=2, fat_g=3), 2).calories_kcal is None


def test_ingredient_rows_match_the_analysis():
    analysis = MockVisionService().analyze_image(b"x")
    rows = ingredient_rows(analysis)
    assert [r["Ingredient"] for r in rows] == ["Chicken", "Rice", "Broccoli"]
    assert sum(r["Proteins (g)"] for r in rows) == round(analysis.total_macros.protein_g, 1)


def test_macro_rows_list_the_three_macros_in_grams():
    rows = macro_rows(Macros(protein_g=10, carbs_g=20, fat_g=5))
    assert rows == [
        {"Macro": "Proteins", "Grams": 10},
        {"Macro": "Carbs", "Grams": 20},
        {"Macro": "Fats", "Grams": 5},
    ]


def test_macro_rows_are_empty_when_every_macro_is_zero():
    assert macro_rows(Macros(protein_g=0, carbs_g=0, fat_g=0)) == []


def test_recipe_ingredient_lines_add_grams_from_the_analysis():
    analysis = MockVisionService().analyze_image(b"x")
    recipe = Recipe(title="t", used_ingredients=["chicken", "Rice", "salt"], steps=["s"])
    assert recipe_ingredient_lines(recipe, analysis) == ["Chicken : 150 g", "Rice : 180 g", "Salt"]
