"""Area 2: Recipe & Dashboard (the recipe itself comes with issue #9)."""

import pandas as pd
import streamlit as st

from components.macros import render_macros_pie, render_metrics, selected_portions
from contracts import NutritionAnalysis
from utils.nutrition import ingredient_rows, per_portion

_MACRO_COLUMNS = ["Proteins (g)", "Carbs (g)", "Fats (g)"]


def render_recipe_dashboard() -> None:
    st.header("Recipe & Dashboard")
    analysis: NutritionAnalysis | None = st.session_state.get("analysis")
    if analysis is None:
        st.info("Analyze a photo in the Upload & Analysis tab to see the nutrition dashboard.")
        return
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
