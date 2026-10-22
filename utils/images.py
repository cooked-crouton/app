"""Validation and normalisation of user-uploaded images.

Images stay in memory (never written to disk). The decoded pixels are re-encoded as JPEG,
which drops all metadata (EXIF/GPS), applies the camera rotation, flattens transparency
and shrinks large photos before they are sent to the vision model.
"""

import io
from dataclasses import dataclass

from PIL import Image, ImageOps, UnidentifiedImageError

ALLOWED_EXTENSIONS = ("jpg", "jpeg", "png", "webp")
# Streamlit's `server.maxUploadSize` (.streamlit/config.toml, in MB) must match.
MAX_UPLOAD_BYTES = 10 * 1024 * 1024
MAX_PIXELS = 40_000_000
MAX_SIDE = 1024
JPEG_QUALITY = 85

_ALLOWED_FORMATS = {"JPEG", "PNG", "WEBP"}
_FORMAT_HINT = "Please upload a JPG, PNG or WebP photo."


class ImageError(ValueError):
    """The upload was rejected. The message is safe to show to the user."""


@dataclass(frozen=True)
class PreparedImage:
    """An uploaded image, validated and re-encoded as JPEG."""

    data: bytes
    width: int
    height: int
    original_bytes: int


def prepare_image(data: bytes) -> PreparedImage:
    """Validate raw upload bytes and return a resized, metadata-free JPEG.

    The check is on the file content, not on its name or declared type.
    """
    if not data:
        raise ImageError("The file is empty.")
    if len(data) > MAX_UPLOAD_BYTES:
        raise ImageError(
            f"The file is too large ({len(data) / 1024 / 1024:.1f} MB). "
            f"The maximum is {MAX_UPLOAD_BYTES // 1024 // 1024} MB."
        )
    try:
        with Image.open(io.BytesIO(data)) as source:
            if source.format not in _ALLOWED_FORMATS:
                raise ImageError(f"Unsupported image format. {_FORMAT_HINT}")
            if source.width * source.height > MAX_PIXELS:
                raise ImageError(
                    f"The image is too large ({source.width}x{source.height} px). "
                    "Please upload a smaller photo."
                )
            image = ImageOps.exif_transpose(source)
            image.load()
            image = _to_rgb(image)
    except ImageError:
        raise
    except (UnidentifiedImageError, Image.DecompressionBombError, OSError, ValueError, SyntaxError):
        raise ImageError(f"This file is not a valid image. {_FORMAT_HINT}") from None

    image.thumbnail((MAX_SIDE, MAX_SIDE), Image.Resampling.LANCZOS)
    out = io.BytesIO()
    image.save(out, format="JPEG", quality=JPEG_QUALITY, optimize=True)
    return PreparedImage(
        data=out.getvalue(),
        width=image.width,
        height=image.height,
        original_bytes=len(data),
    )


def _to_rgb(image: Image.Image) -> Image.Image:
    """Convert to RGB, flattening any transparency onto white."""
    if image.mode == "RGB":
        return image
    rgba = image.convert("RGBA")
    flat = Image.new("RGB", rgba.size, "white")
    flat.paste(rgba, mask=rgba.getchannel("A"))
    return flat
