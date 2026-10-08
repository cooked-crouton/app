"""Streamlit entry point: `streamlit run app.py`."""

import streamlit as st

from config import settings
from ui.chat import render_chat
from ui.recipe_dashboard import render_recipe_dashboard
from ui.sidebar import render_sidebar
from ui.upload_analysis import render_upload_analysis

st.set_page_config(page_title="Cooked Crouton", page_icon="🥖", layout="wide")

render_sidebar(settings)

upload_tab, recipe_tab, chat_tab = st.tabs(
    ["Upload & Analysis", "Recipe & Dashboard", "Chat"]
)
with upload_tab:
    render_upload_analysis()
with recipe_tab:
    render_recipe_dashboard()
with chat_tab:
    render_chat()
