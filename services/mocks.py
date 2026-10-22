"""Fake services returning realistic French data, so the UI can be built before the real
modules exist. Outputs are validated by the same Pydantic contracts as the real ones."""

import time

from contracts import (
    AnalyzeIngredientsRequest,
    ChatData,
    ChatRequest,
    CookingState,
    DetectedIngredient,
    Macros,
    NutritionAnalysis,
    Recipe,
    RecipeRequest,
    RecipeResponse,
    Source,
)

# (protein_g, carbs_g, fat_g, kcal) per 100 g, approximate values for cooked/raw food.
_PER_100G: dict[str, tuple[float, float, float, float]] = {
    "poulet": (27.0, 0.0, 7.0, 165.0),
    "riz": (2.7, 28.0, 0.3, 130.0),
    "brocoli": (2.8, 7.0, 0.4, 35.0),
    "pâtes": (5.0, 25.0, 1.1, 131.0),
    "œufs": (13.0, 1.1, 11.0, 155.0),
    "tomates": (0.9, 3.9, 0.2, 18.0),
    "oignon": (1.1, 9.3, 0.1, 40.0),
}
_UNKNOWN_PER_100G = (5.0, 15.0, 5.0, 120.0)

# What the mock "sees" on any photo.
_PLATE: list[tuple[str, float, CookingState]] = [
    ("poulet", 150.0, CookingState.GRILLED),
    ("riz", 180.0, CookingState.BOILED),
    ("brocoli", 100.0, CookingState.STEAMED),
]


def _macros(name: str, grams: float) -> Macros:
    protein, carbs, fat, kcal = _PER_100G.get(name.strip().lower(), _UNKNOWN_PER_100G)
    k = grams / 100
    return Macros(
        protein_g=round(protein * k, 1),
        carbs_g=round(carbs * k, 1),
        fat_g=round(fat * k, 1),
        calories_kcal=round(kcal * k, 1),
    )


def _total(items: list[Macros], divisor: int = 1) -> Macros:
    return Macros(
        protein_g=round(sum(m.protein_g for m in items) / divisor, 1),
        carbs_g=round(sum(m.carbs_g for m in items) / divisor, 1),
        fat_g=round(sum(m.fat_g for m in items) / divisor, 1),
        calories_kcal=round(sum(m.calories_kcal or 0 for m in items) / divisor, 1),
    )


def _analysis(items: list[tuple[str, float, CookingState]], portions: int) -> NutritionAnalysis:
    ingredients = [
        DetectedIngredient(
            name=name,
            estimated_grams=grams,
            cooking_state=state,
            confidence=0.9,
            macros=_macros(name, grams),
        )
        for name, grams, state in items
    ]
    all_macros = [i.macros for i in ingredients]
    return NutritionAnalysis(
        ingredients=ingredients,
        total_macros=_total(all_macros),
        portions=portions,
        macros_per_portion=_total(all_macros, portions),
    )


class MockVisionService:
    """Stands in for vision_engine. `delay` simulates its (slow) inference."""

    def __init__(self, delay: float = 0.0) -> None:
        self._delay = delay

    def analyze_image(self, image: bytes, portions: int = 1) -> NutritionAnalysis:
        if not image:
            raise ValueError("Image vide.")
        time.sleep(self._delay)
        return _analysis(_PLATE, portions)

    def analyze_ingredients(self, request: AnalyzeIngredientsRequest) -> NutritionAnalysis:
        time.sleep(self._delay)
        items = [(i.name, i.grams or 100.0, i.cooking_state) for i in request.ingredients]
        return _analysis(items, request.portions)


class MockRecipeService:
    """Stands in for Rag_llm `POST /api/v1/generate`."""

    def __init__(self, delay: float = 0.0) -> None:
        self._delay = delay

    def generate(self, request: RecipeRequest) -> RecipeResponse:
        time.sleep(self._delay)
        names = ", ".join(request.ingredients)
        suffix = f" ({', '.join(request.dietary_constraints)})" if request.dietary_constraints else ""
        return RecipeResponse(
            recipe=Recipe(
                title=f"Poêlée de {', '.join(request.ingredients[:3])}{suffix}",
                cook_time="20 min",
                used_ingredients=list(request.ingredients),
                steps=[
                    f"Laver et couper les ingrédients : {names}.",
                    "Faire chauffer un filet d'huile dans une poêle à feu moyen.",
                    "Faire revenir les ingrédients pendant 10 minutes en remuant.",
                    "Assaisonner de sel et de poivre, laisser mijoter 5 minutes.",
                    "Servir chaud.",
                ],
                emissions_kgco2eq=0.0000385,
            )
        )


class MockChatService:
    """Stands in for Rag_llm `POST /api/v1/chat`. Always returns a sourced answer."""

    def __init__(self, delay: float = 0.0) -> None:
        self._delay = delay

    def ask(self, request: ChatRequest) -> ChatData:
        time.sleep(self._delay)
        return ChatData(
            response=(
                "Pour alléger la recette, vous pouvez remplacer le beurre par du fromage "
                "blanc 0% ou du yaourt grec. Pour une sauce, un peu d'eau de cuisson liée "
                "avec une touche de fromage frais fonctionne aussi très bien."
            ),
            sources=[
                Source(
                    title="Pâtes Carbonara Traditionnelles",
                    url="https://www.marmiton.org/recettes/recette_pates-carbonara_12345.aspx",
                ),
                Source(title="Gratin de courgettes allégé"),
            ],
            emissions_kgco2eq=0.0000215,
        )
