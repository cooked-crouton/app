"""Area 2: Recipe & Dashboard."""

import pandas as pd
import streamlit as st

from components.macros import render_macros_pie, render_metrics, selected_portions
from config import settings
from contracts import NutritionAnalysis, Recipe, RecipeRequest
from services.factory import get_services
from utils.nutrition import ingredient_rows, per_portion, recipe_ingredient_lines
from utils.streaming import stream_text

_MACRO_COLUMNS = ["Proteins (g)", "Carbs (g)", "Fats (g)"]


def render_recipe_dashboard() -> None:
    st.header("Recipe & Dashboard")
    analysis: NutritionAnalysis | None = st.session_state.get("analysis")
    if analysis is None:
        st.info("Analyze a photo in the Upload & Analysis tab to see the nutrition dashboard.")
        return
    _render_recipe(analysis)
    portions = selected_portions(analysis)
    scope = st.radio(
        "Show", ["Per portion", "Whole dish"], horizontal=True, key="dashboard_scope"
    )
    macros = (
        per_portion(analysis.total_macros, portions)
        if scope == "Per portion"
        else analysis.total_macros
    )
    st.subheader("Macros")
    if scope == "Per portion":
        st.caption(f"{portions} portion{'s' if portions > 1 else ''}")
    render_metrics(macros)
    render_macros_pie(macros)
    st.subheader("Contribution of each ingredient (whole dish)")
    rows = pd.DataFrame(ingredient_rows(analysis))
    st.bar_chart(rows, x="Ingredient", y=_MACRO_COLUMNS, y_label="Grams")


def _render_recipe(analysis: NutritionAnalysis) -> None:
    """Generate button, then the recipe (title, ingredients, numbered steps)."""
    recipe: Recipe | None = st.session_state.get("recipe")
    if st.button("Regenerate recipe" if recipe else "Generate recipe", type="primary"):
        _generate(analysis)
    fresh = st.session_state.pop("recipe_fresh", False)
    if recipe is None:
        st.caption("Generate a recipe from the ingredients of the analysis.")
        return
    st.subheader(recipe.title)
    if recipe.cook_time:
        st.caption(f"Cooking time: {recipe.cook_time}")
    st.markdown("**Ingredients**")
    st.markdown("\n".join(f"- {line}" for line in recipe_ingredient_lines(recipe, analysis)))
    st.markdown("**Steps**")
    for number, step in enumerate(recipe.steps, start=1):
        text = f"{number}. {step}"
        if fresh:
            st.write_stream(stream_text(text))
        else:
            st.markdown(text)


def _generate(analysis: NutritionAnalysis) -> None:
    recipes = get_services(settings).recipe
    try:
        with st.spinner("Generating the recipe..."):
            response = recipes.generate(RecipeRequest.from_analysis(analysis))
    except Exception:  # noqa: BLE001 - shown to the user, never a traceback
        st.error("The recipe could not be generated. Check that the recipe service is running.")
        return
    st.session_state["recipe"] = response.recipe
    st.session_state["recipe_fresh"] = True  # stream it on the next run
    st.rerun()
