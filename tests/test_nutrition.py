from contracts import Macros
from services.mocks import MockVisionService
from utils.nutrition import ingredient_rows, per_portion


def test_per_portion_divides_every_value():
    total = Macros(protein_g=40, carbs_g=60, fat_g=20, calories_kcal=600)
    assert per_portion(total, 4) == Macros(protein_g=10, carbs_g=15, fat_g=5, calories_kcal=150)


def test_per_portion_keeps_unknown_calories_unknown():
    assert per_portion(Macros(protein_g=1, carbs_g=2, fat_g=3), 2).calories_kcal is None


def test_ingredient_rows_match_the_analysis():
    analysis = MockVisionService().analyze_image(b"x")
    rows = ingredient_rows(analysis)
    assert [r["Ingredient"] for r in rows] == ["Poulet", "Riz", "Brocoli"]
    assert sum(r["Proteins (g)"] for r in rows) == round(analysis.total_macros.protein_g, 1)
