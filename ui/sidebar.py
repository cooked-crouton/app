"""Sidebar: app title and current (read-only) configuration."""

import streamlit as st

from config import Settings


def render_sidebar(settings: Settings) -> None:
    with st.sidebar:
        st.title("🥖 Cooked Crouton")
        st.caption("Local, private recipe assistant")
        st.divider()
        st.subheader("Configuration")
        st.text(f"Ollama: {settings.ollama_url}")
        st.text(f"Vision model: {settings.vision_model}")
        st.text(f"Chat model: {settings.chat_model}")
