"""Run the (slow) image analysis in the background and turn failures into user messages."""

import logging
import threading
import time
from collections.abc import Callable
from typing import Literal

from config import Settings
from contracts import (
    NutritionAnalysis,
    VisionModelNotFoundError,
    VisionTimeoutError,
    VisionUnavailableError,
)

logger = logging.getLogger(__name__)

JobState = Literal["running", "done", "failed", "cancelled", "timeout"]


class AnalysisJob:
    """Runs `func` in a daemon thread. The UI polls `state`, it never blocks on the call.

    Python cannot kill a thread, so `cancel()` and a timeout only make the job ignore the
    eventual result: the UI is released, the underlying call finishes in the background.
    """

    def __init__(self, func: Callable[[], NutritionAnalysis], timeout_s: float) -> None:
        self._func = func
        self._timeout_s = timeout_s
        self._started = time.monotonic()
        self._cancelled = threading.Event()
        self._finished = threading.Event()
        self._result: NutritionAnalysis | None = None
        self._error: Exception | None = None
        threading.Thread(target=self._run, daemon=True).start()

    def _run(self) -> None:
        try:
            self._result = self._func()
        except Exception as exc:  # noqa: BLE001 - reported to the UI via `error`
            logger.exception("Image analysis failed")
            self._error = exc
        finally:
            self._finished.set()

    def cancel(self) -> None:
        self._cancelled.set()

    @property
    def elapsed(self) -> float:
        return time.monotonic() - self._started

    @property
    def state(self) -> JobState:
        if self._cancelled.is_set():
            return "cancelled"
        if self._finished.is_set():
            return "failed" if self._error is not None else "done"
        if self.elapsed > self._timeout_s:
            return "timeout"
        return "running"

    @property
    def result(self) -> NutritionAnalysis | None:
        return self._result

    @property
    def error(self) -> Exception | None:
        return self._error


def describe_error(exc: Exception, settings: Settings) -> str:
    """An actionable, user-facing message for a failed analysis."""
    model = settings.vision_model
    if isinstance(exc, VisionUnavailableError):
        return (
            f"Cannot reach Ollama at {settings.ollama_url}. "
            "Start it (`ollama serve`) and try again."
        )
    if isinstance(exc, VisionModelNotFoundError):
        return f"The vision model '{model}' is not installed. Run `ollama pull {model}`."
    if isinstance(exc, VisionTimeoutError):
        return "The analysis took too long. Try a smaller photo or try again."
    if isinstance(exc, ValueError):
        return str(exc)
    return "The analysis failed unexpectedly. Check the application logs and try again."


def timeout_message(timeout_s: float) -> str:
    return f"No answer after {timeout_s:.0f} s. Check that Ollama is running, then try again."
