"""Area 1: Upload & Analysis."""

import time

import streamlit as st

from components.image_upload import render_image_upload
from config import settings
from contracts import NutritionAnalysis
from services.analysis import AnalysisJob, describe_error, timeout_message
from services.factory import get_services
from utils.images import PreparedImage

_POLL_SECONDS = 0.3
_REVEAL_SECONDS = 0.25  # pause between ingredients when a fresh result is revealed


def render_upload_analysis() -> None:
    st.header("Upload & Analysis")
    image = render_image_upload()
    if image is None:
        return
    job: AnalysisJob | None = st.session_state.get("analysis_job")
    if job is not None:
        _render_running(job)
        return
    _render_controls(image)
    notice = st.session_state.get("analysis_notice")
    if notice:
        level, message = notice
        (st.error if level == "error" else st.info)(message)
    analysis: NutritionAnalysis | None = st.session_state.get("analysis")
    if analysis is not None:
        _render_ingredients(analysis, animate=st.session_state.pop("analysis_fresh", False))


def _render_controls(image: PreparedImage) -> None:
    has_result = st.session_state.get("analysis") is not None
    portions = st.number_input("Portions", min_value=1, max_value=12, value=1, key="portions")
    if st.button("Analyze again" if has_result else "Analyze image", type="primary"):
        st.session_state.pop("analysis", None)
        st.session_state.pop("analysis_notice", None)
        vision = get_services(settings).vision
        st.session_state["analysis_job"] = AnalysisJob(
            lambda: vision.analyze_image(image.data, int(portions)),
            timeout_s=settings.vision_timeout_s,
        )
        st.rerun()


def _render_running(job: AnalysisJob) -> None:
    """Show progress while the job runs; on any other state, store the outcome and rerun."""
    if "portions" in st.session_state:  # keep the widget value while it is not rendered
        st.session_state["portions"] = st.session_state["portions"]
    state = job.state
    if state == "running":
        with st.status(f"Analysing the image... {job.elapsed:.0f} s", expanded=True):
            st.write("The vision model is identifying ingredients and estimating weights.")
        if st.button("Cancel analysis"):
            job.cancel()
            st.rerun()
        time.sleep(_POLL_SECONDS)
        st.rerun()
    elif state == "done":
        st.session_state["analysis"] = job.result
        st.session_state["analysis_fresh"] = True
    elif state == "failed":
        st.session_state["analysis_notice"] = ("error", describe_error(job.error, settings))
    elif state == "timeout":
        job.cancel()  # ignore the late result
        st.session_state["analysis_notice"] = ("error", timeout_message(settings.vision_timeout_s))
    else:  # cancelled
        st.session_state["analysis_notice"] = ("info", "Analysis cancelled.")
    st.session_state.pop("analysis_job", None)
    st.rerun()


def _render_ingredients(analysis: NutritionAnalysis, animate: bool) -> None:
    st.subheader("Detected ingredients")
    rows = [
        {
            "Ingredient": ing.name.capitalize(),
            "Cooking state": ing.cooking_state.value.capitalize(),
            "Estimated weight (g)": round(ing.estimated_grams),
            "Confidence": f"{ing.confidence:.0%}" if ing.confidence is not None else "-",
        }
        for ing in analysis.ingredients
    ]
    if not animate:
        st.table(rows)
        return
    table = st.empty()
    for count in range(1, len(rows) + 1):
        table.table(rows[:count])
        time.sleep(_REVEAL_SECONDS)
