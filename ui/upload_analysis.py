"""Area 1: Upload & Analysis."""

import streamlit as st

from components.image_upload import render_image_upload


def render_upload_analysis() -> None:
    st.header("Upload & Analysis")
    image = render_image_upload()
    if image is not None:
        st.info("Image ready. The analysis comes in a following step.")
