"""Affiliate Auto Tool — local-first Streamlit application entry point."""

import streamlit as st

st.set_page_config(page_title="Affiliate Auto Tool", page_icon=":material/rocket_launch:", layout="wide")

for key, value in {
    "selected_product": None,
    "latest_content": None,
    "latest_media": None,
    "research_results": [],
}.items():
    st.session_state.setdefault(key, value)

pages = {
    "Workspace": [
        st.Page("app_pages/dashboard.py", title="Dashboard", icon=":material/dashboard:", default=True),
        st.Page("app_pages/research.py", title="Product research", icon=":material/travel_explore:"),
        st.Page("app_pages/winners.py", title="Winner finder", icon=":material/emoji_events:"),
    ],
    "Production": [
        st.Page("app_pages/content.py", title="Content studio", icon=":material/edit_note:"),
        st.Page("app_pages/video.py", title="Video studio", icon=":material/movie:"),
        st.Page("app_pages/ready_to_post.py", title="Ready to post", icon=":material/inventory_2:"),
    ],
    "Learn & manage": [
        st.Page("app_pages/analytics.py", title="Analytics", icon=":material/analytics:"),
        st.Page("app_pages/assistant.py", title="AI assistant", icon=":material/smart_toy:"),
        st.Page("app_pages/settings.py", title="Settings", icon=":material/settings:"),
    ],
}

with st.sidebar:
    st.title("Affiliate Auto Tool")
    st.caption("Local-first affiliate workflow")
    st.badge("MVP", icon=":material/rocket_launch:", color="blue")

st.navigation(pages, position="sidebar").run()
