"""Image upload widget: drag & drop, validation, preview, replace/remove."""

import streamlit as st

from utils.images import ALLOWED_EXTENSIONS, ImageError, PreparedImage, prepare_image

IMAGE_KEY = "image"  # st.session_state key holding the current `PreparedImage`
_NONCE_KEY = "upload_nonce"  # changing the uploader key is how a file_uploader is reset


# Streamlit has no size option for the drop zone, so it is enlarged with local CSS.
_DROPZONE_CSS = """
<style>
[data-testid="stFileUploaderDropzone"] {
    min-height: 16rem;
    justify-content: center;
    border-width: 2px;
    border-style: dashed;
}
</style>
"""


def get_current_image() -> PreparedImage | None:
    """The image currently loaded by the user, if any."""
    return st.session_state.get(IMAGE_KEY)


def clear_image() -> None:
    """Forget the current image and any result computed from it."""
    st.session_state.pop(IMAGE_KEY, None)
    st.session_state.pop("analysis", None)  # filled by the analysis step
    st.session_state[_NONCE_KEY] = st.session_state.get(_NONCE_KEY, 0) + 1


def render_image_upload() -> PreparedImage | None:
    """Show the uploader, or the preview of the loaded image. Returns the current image."""
    image = get_current_image()
    if image is None:
        st.markdown(_DROPZONE_CSS, unsafe_allow_html=True)
        uploaded = st.file_uploader(
            "Drop a photo of your fridge or dish",
            type=list(ALLOWED_EXTENSIONS),
            key=f"uploader_{st.session_state.get(_NONCE_KEY, 0)}",
            help="JPG, PNG or WebP, up to 10 MB. Large photos are resized automatically.",
        )
        if uploaded is None:
            return None
        try:
            image = prepare_image(uploaded.getvalue())
        except ImageError as exc:
            st.error(str(exc))
            return None
        st.session_state.pop("analysis", None)
        st.session_state[IMAGE_KEY] = image
        st.rerun()

    st.image(
        image.data,
        caption=f"{image.width}x{image.height} px, {len(image.data) / 1024:.0f} KB "
        f"(original {image.original_bytes / 1024:.0f} KB)",
        width="stretch",
    )
    if st.button("Remove / replace image"):
        clear_image()
        st.rerun()
    return image
