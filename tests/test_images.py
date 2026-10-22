import io

import pytest
from PIL import Image

from utils import images
from utils.images import ImageError, prepare_image


def _encode(fmt: str, size=(200, 100), mode="RGB", color="red", **save_kwargs) -> bytes:
    buf = io.BytesIO()
    Image.new(mode, size, color).save(buf, format=fmt, **save_kwargs)
    return buf.getvalue()


def _decode(data: bytes) -> Image.Image:
    return Image.open(io.BytesIO(data))


@pytest.mark.parametrize("fmt", ["JPEG", "PNG", "WEBP"])
def test_accepted_formats_become_jpeg(fmt):
    out = prepare_image(_encode(fmt))
    assert _decode(out.data).format == "JPEG"
    assert (out.width, out.height) == (200, 100)


def test_large_image_is_resized_keeping_aspect_ratio():
    out = prepare_image(_encode("PNG", size=(3000, 1500)))
    assert max(out.width, out.height) == images.MAX_SIDE
    assert out.width == 2 * out.height


def test_small_image_is_not_upscaled():
    assert prepare_image(_encode("PNG", size=(50, 40))).width == 50


def test_transparency_is_flattened_on_white():
    out = prepare_image(_encode("PNG", mode="RGBA", color=(255, 0, 0, 0)))
    assert _decode(out.data).convert("RGB").getpixel((5, 5)) == (255, 255, 255)


def test_exif_rotation_applied_and_metadata_dropped():
    exif = Image.Exif()
    exif[0x0112] = 6  # rotate 90 degrees
    exif[0x010F] = "SecretCameraBrand"
    out = prepare_image(_encode("JPEG", size=(200, 100), exif=exif))
    assert (out.width, out.height) == (100, 200)
    assert len(_decode(out.data).getexif()) == 0
    assert b"SecretCameraBrand" not in out.data


def test_content_is_checked_not_the_extension():
    with pytest.raises(ImageError, match="not a valid image"):
        prepare_image(b"<html>not an image.jpg</html>")


def test_unsupported_format_rejected():
    with pytest.raises(ImageError, match="Unsupported"):
        prepare_image(_encode("GIF"))


def test_truncated_image_rejected():
    with pytest.raises(ImageError, match="not a valid image"):
        prepare_image(_encode("PNG", size=(500, 500))[:100])


def test_empty_file_rejected():
    with pytest.raises(ImageError, match="empty"):
        prepare_image(b"")


def test_oversized_file_rejected_before_decoding(monkeypatch):
    monkeypatch.setattr(images, "MAX_UPLOAD_BYTES", 1024)
    with pytest.raises(ImageError, match="too large"):
        prepare_image(b"0" * 2048)


def test_too_many_pixels_rejected(monkeypatch):
    monkeypatch.setattr(images, "MAX_PIXELS", 1000)
    with pytest.raises(ImageError, match="too large"):
        prepare_image(_encode("PNG", size=(100, 100)))
