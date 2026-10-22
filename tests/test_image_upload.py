import io
from pathlib import Path

from PIL import Image
from streamlit.testing.v1 import AppTest


APP = str(Path(__file__).resolve().parent.parent / "app.py")


def _app() -> AppTest:
    return AppTest.from_file(APP, default_timeout=30).run()


def _png(size=(120, 80)) -> bytes:
    buf = io.BytesIO()
    Image.new("RGB", size, "green").save(buf, format="PNG")
    return buf.getvalue()


def test_starts_with_an_empty_uploader():
    at = _app()
    assert not at.exception
    assert len(at.file_uploader) == 1
    assert len(at.button) == 0


def test_valid_upload_shows_preview_and_hides_uploader():
    at = _app()
    at.file_uploader[0].upload("photo.png", _png(), "image/png").run()
    assert not at.exception
    assert len(at.file_uploader) == 0
    assert at.session_state["image"].width == 120
    assert any(b.label == "Remove / replace image" for b in at.button)


def test_fake_image_shows_clear_error_and_keeps_uploader():
    at = _app()
    at.file_uploader[0].upload("evil.png", b"<script>alert(1)</script>", "image/png").run()
    assert not at.exception
    assert any("not a valid image" in e.value for e in at.error)
    assert "image" not in at.session_state
    assert len(at.file_uploader) == 1


def test_remove_resets_to_a_fresh_uploader():
    at = _app()
    at.file_uploader[0].upload("photo.png", _png(), "image/png").run()
    next(b for b in at.button if b.label == "Remove / replace image").click().run()
    assert not at.exception
    assert "image" not in at.session_state
    assert len(at.file_uploader) == 1 and at.file_uploader[0].value is None


def test_replacing_an_image_discards_the_previous_analysis():
    at = _app()
    at.file_uploader[0].upload("photo.png", _png(), "image/png").run()
    at.session_state["analysis"] = "stale"
    next(b for b in at.button if b.label == "Remove / replace image").click().run()
    assert "analysis" not in at.session_state
