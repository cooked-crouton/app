"""Area 1: Upload & Analysis."""

import time

import pandas as pd
import streamlit as st

from components.image_upload import render_image_upload
from config import settings
from contracts import AnalyzeIngredientsRequest, CookingState, NutritionAnalysis
from services.analysis import AnalysisJob, describe_error, timeout_message
from services.factory import get_services
from utils.images import PreparedImage
from utils.ingredients import GRAMS, NAME, STATE, to_request, to_rows

_POLL_SECONDS = 0.3
_REVEAL_SECONDS = 0.25  # pause between ingredients when a fresh result is revealed


def render_upload_analysis() -> None:
    st.header("Upload & Analysis")
    image = render_image_upload()
    if image is None:
        return
    job: AnalysisJob | None = st.session_state.get("analysis_job")
    if job is not None:
        _render_running()
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


@st.fragment(run_every=_POLL_SECONDS)
def _render_running() -> None:
    """Show progress while the job runs. Only this fragment reruns, so the other tabs stay
    usable; once the job ends, store the outcome and rerun the whole app."""
    job: AnalysisJob | None = st.session_state.get("analysis_job")
    if job is None:
        st.rerun()
    if "portions" in st.session_state:  # keep the widget value while it is not rendered
        st.session_state["portions"] = st.session_state["portions"]
    state = job.state
    if state == "running":
        with st.status(f"Analysing the image... {job.elapsed:.0f} s", expanded=True):
            st.write("The vision model is identifying ingredients and estimating weights.")
        if st.button("Cancel analysis"):
            job.cancel()
            st.rerun()
        return
    if state == "done":
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
    """Editable table: the validated list is `analysis`, recomputed after every edit."""
    st.subheader("Detected ingredients")
    rows = to_rows(analysis)
    if animate:
        table = st.empty()
        for count in range(1, len(rows) + 1):
            table.table(rows[:count])
            time.sleep(_REVEAL_SECONDS)
        table.empty()
    st.caption("Correct the list if needed: rename, change a weight, add or remove a row.")
    edited = st.data_editor(
        pd.DataFrame(rows, columns=[NAME, STATE, GRAMS]),
        num_rows="dynamic",
        hide_index=True,
        column_config={
            NAME: st.column_config.TextColumn(required=True),
            STATE: st.column_config.SelectboxColumn(options=[s.value for s in CookingState]),
            GRAMS: st.column_config.NumberColumn(min_value=1, format="%.0f"),
        },
    )
    edited_rows = edited.to_dict("records")
    if edited_rows == rows:
        return
    request = to_request(edited_rows, analysis.portions)
    if request is None:
        st.warning("Keep at least one ingredient.")
        return
    _recompute(request)


def _recompute(request: AnalyzeIngredientsRequest) -> None:
    """Replace the analysis by the one computed from the edited list."""
    vision = get_services(settings).vision
    try:
        with st.spinner("Updating nutrition..."):
            st.session_state["analysis"] = vision.analyze_ingredients(request)
    except Exception as exc:  # noqa: BLE001 - shown to the user
        st.error(describe_error(exc, settings))
        return
    st.rerun()
