"""Macros widgets shared by the analysis and dashboard areas."""

import altair as alt
import streamlit as st

from contracts import Macros, NutritionAnalysis
from utils.nutrition import ingredient_macro_rows, macro_rows


def selected_portions(analysis: NutritionAnalysis) -> int:
    """Number of portions chosen in the selector (the analysis' own value as fallback)."""
    return int(st.session_state.get("portions", analysis.portions))


def render_metrics(macros: Macros) -> None:
    kcal = macros.calories_kcal
    cols = st.columns(4)
    cols[0].metric("Calories", "-" if kcal is None else f"{kcal:.0f} kcal")
    cols[1].metric("Proteins", f"{macros.protein_g:.1f} g")
    cols[2].metric("Carbs", f"{macros.carbs_g:.1f} g")
    cols[3].metric("Fats", f"{macros.fat_g:.1f} g")


def render_macros_pie(macros: Macros) -> None:
    """Donut of proteins / carbs / fats in grams."""
    rows = macro_rows(macros)
    if not rows:
        st.info("No macros to chart (all values are 0).")
        return
    chart = (
        alt.Chart(alt.Data(values=rows))
        .mark_arc(innerRadius=60)
        .encode(
            theta=alt.Theta("Grams:Q"),
            color=alt.Color("Macro:N", sort=["Proteins", "Carbs", "Fats"]),
            tooltip=["Macro:N", alt.Tooltip("Grams:Q", format=".1f")],
        )
    )
    st.altair_chart(chart, width="stretch")


_BAR_HEIGHT_PX = 36  # per ingredient, so the chart never needs an inner scrollbar


def render_ingredient_bars(analysis: NutritionAnalysis) -> None:
    """Static horizontal stacked bars: grams of each macro brought by each ingredient."""
    rows = ingredient_macro_rows(analysis)
    chart = (
        alt.Chart(alt.Data(values=rows))
        .mark_bar()
        .encode(
            y=alt.Y("Ingredient:N", sort=None, title=None),
            x=alt.X("Grams:Q", title="Grams"),
            color=alt.Color("Macro:N", sort=["Proteins", "Carbs", "Fats"]),
            tooltip=["Ingredient:N", "Macro:N", alt.Tooltip("Grams:Q", format=".1f")],
        )
        .properties(height=_BAR_HEIGHT_PX * len(analysis.ingredients) + 50)
    )
    st.altair_chart(chart, width="stretch")
