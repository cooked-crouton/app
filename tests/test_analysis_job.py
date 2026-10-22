import threading
import time

import pytest

import config
from contracts import (
    VisionModelNotFoundError,
    VisionTimeoutError,
    VisionUnavailableError,
)
from services.analysis import AnalysisJob, describe_error, timeout_message
from services.mocks import MockVisionService


def _wait(job: AnalysisJob, timeout=2.0):
    end = time.monotonic() + timeout
    while job.state == "running" and time.monotonic() < end:
        time.sleep(0.01)


def _analysis():
    return MockVisionService().analyze_image(b"x")


def test_job_completes_with_result():
    job = AnalysisJob(_analysis, timeout_s=5)
    _wait(job)
    assert job.state == "done" and len(job.result.ingredients) == 3 and job.error is None


def test_job_reports_failure():
    def boom():
        raise VisionUnavailableError()

    job = AnalysisJob(boom, timeout_s=5)
    _wait(job)
    assert job.state == "failed" and isinstance(job.error, VisionUnavailableError)


def test_cancel_wins_over_a_late_result():
    gate = threading.Event()

    def slow():
        gate.wait(2)
        return _analysis()

    job = AnalysisJob(slow, timeout_s=5)
    assert job.state == "running"
    job.cancel()
    gate.set()
    time.sleep(0.1)
    assert job.state == "cancelled"


def test_job_times_out():
    gate = threading.Event()
    job = AnalysisJob(lambda: (gate.wait(2), _analysis())[1], timeout_s=0.05)
    time.sleep(0.15)
    assert job.state == "timeout"
    gate.set()


@pytest.mark.parametrize(
    "exc,expected",
    [
        (VisionUnavailableError(), "ollama serve"),
        (VisionModelNotFoundError(), "ollama pull llava"),
        (VisionTimeoutError(), "too long"),
        (ValueError("Empty image."), "Empty image."),
        (RuntimeError("secret internal detail"), "unexpectedly"),
    ],
)
def test_describe_error_is_actionable(exc, expected):
    msg = describe_error(exc, config.load_settings())
    assert expected in msg
    assert "secret internal detail" not in msg


def test_timeout_message_mentions_duration():
    assert "120 s" in timeout_message(120)
