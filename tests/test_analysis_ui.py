import io
import threading
import time
from pathlib import Path

import pytest
from PIL import Image
from streamlit.testing.v1 import AppTest

import ui.upload_analysis as panel
from contracts import VisionModelNotFoundError, VisionUnavailableError
from services.factory import Services
from services.mocks import MockChatService, MockRecipeService, MockVisionService

APP = str(Path(__file__).resolve().parent.parent / "app.py")


def _png() -> bytes:
    buf = io.BytesIO()
    Image.new("RGB", (120, 80), "green").save(buf, format="PNG")
    return buf.getvalue()


def _use_vision(monkeypatch, vision) -> None:
    services = Services(vision=vision, recipe=MockRecipeService(), chat=MockChatService())
    monkeypatch.setattr(panel, "get_services", lambda _settings: services)


def _uploaded() -> AppTest:
    at = AppTest.from_file(APP, default_timeout=30).run()
    at.file_uploader[0].upload("photo.png", _png(), "image/png").run()
    return at


def _click(at: AppTest, label: str) -> AppTest:
    return next(b for b in at.button if b.label == label).click().run()


def _settle(at: AppTest) -> AppTest:
    """AppTest has no timer: wait for the job to end, then rerun like the fragment would."""
    if "analysis_job" not in at.session_state:  # the first run already stored the outcome
        return at
    job = at.session_state["analysis_job"]
    while job.state == "running":
        time.sleep(0.01)
    return at.run()


def test_analyze_shows_ingredients_with_state_and_grams(monkeypatch):
    _use_vision(monkeypatch, MockVisionService())
    at = _settle(_click(_uploaded(), "Analyze image"))
    assert not at.exception
    rows = at.table[0].value
    assert list(rows["Ingredient"]) == ["Poulet", "Riz", "Brocoli"]
    assert list(rows["Cooking state"]) == ["Grilled", "Boiled", "Steamed"]
    assert list(rows["Estimated weight (g)"]) == [150, 180, 100]
    assert at.session_state["analysis"].portions == 1


def test_portions_are_passed_to_the_service(monkeypatch):
    _use_vision(monkeypatch, MockVisionService())
    at = _uploaded()
    at.number_input(key="portions").set_value(3).run()
    at = _settle(_click(at, "Analyze image"))
    assert at.session_state["analysis"].portions == 3


@pytest.mark.parametrize(
    "error,expected",
    [
        (VisionUnavailableError(), "ollama serve"),
        (VisionModelNotFoundError(), "ollama pull"),
        (RuntimeError("boom"), "unexpectedly"),
    ],
)
def test_failures_show_actionable_messages(monkeypatch, error, expected):
    _use_vision(monkeypatch, MockVisionService(error=error))
    at = _settle(_click(_uploaded(), "Analyze image"))
    assert not at.exception
    assert any(expected in e.value for e in at.error)
    assert "analysis" not in at.session_state
    assert any(b.label == "Analyze image" for b in at.button)  # can retry


def test_running_job_shows_progress_and_cancel_releases_the_ui(monkeypatch):
    gate = threading.Event()

    class Blocking(MockVisionService):
        def analyze_image(self, image, portions=1):
            gate.wait(5)
            return super().analyze_image(image, portions)

    _use_vision(monkeypatch, Blocking())
    try:
        at = _click(_uploaded(), "Analyze image")
        assert not at.exception
        assert len(at.tabs) == 3 and at.header  # other tabs still render while running
        assert [s.label for s in at.status][0].startswith("Analysing the image")
        assert any(b.label == "Cancel analysis" for b in at.button)

        at = _click(at, "Cancel analysis")
        assert not at.exception
        assert "analysis_job" not in at.session_state and "analysis" not in at.session_state
        assert any("cancelled" in i.value for i in at.info)
        assert any(b.label == "Analyze image" for b in at.button)  # can start again
    finally:
        gate.set()


def test_late_result_after_cancel_is_ignored(monkeypatch):
    gate = threading.Event()

    class Blocking(MockVisionService):
        def analyze_image(self, image, portions=1):
            gate.wait(5)
            return super().analyze_image(image, portions)

    _use_vision(monkeypatch, Blocking())
    try:
        at = _click(_uploaded(), "Analyze image")
        at = _click(at, "Cancel analysis")
        gate.set()
        time.sleep(0.2)
        at = at.run()
        assert "analysis" not in at.session_state
    finally:
        gate.set()


def test_removing_the_image_discards_the_analysis(monkeypatch):
    _use_vision(monkeypatch, MockVisionService())
    at = _settle(_click(_uploaded(), "Analyze image"))
    at = _click(at, "Remove / replace image")
    assert "analysis" not in at.session_state and "image" not in at.session_state
