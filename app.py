import streamlit as st
from config.settings import settings
from core.logging import logger
from ui.dashboard import render_dashboard

def configure_page() -> None:
    st.set_page_config(
        page_title=settings.app_name,
        page_icon="🎙️",
        layout="wide",
        initial_sidebar_state="collapsed",
    )

def main() -> None:
    configure_page()
    logger.info("Starting AI Meeting Intelligence application.")
    render_dashboard()

if __name__ == "__main__":
    main()
