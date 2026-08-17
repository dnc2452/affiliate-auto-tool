"""Affiliate Auto Tool — local-first Streamlit application entry point."""

import streamlit as st

st.set_page_config(page_title="Affiliate Auto Tool", page_icon=":material/rocket_launch:", layout="wide")

for key, value in {
    "selected_product": None,
    "latest_content": None,
    "latest_media": None,
    "research_results": [],
    "content_language": "vi",
    "latest_package": None,
}.items():
    st.session_state.setdefault(key, value)

pages = {
    "Làm việc": [
        st.Page("app_pages/dashboard.py", title="Tổng quan", icon=":material/dashboard:", default=True),
        st.Page("app_pages/research.py", title="Nghiên cứu sản phẩm", icon=":material/travel_explore:"),
        st.Page("app_pages/winners.py", title="Tìm sản phẩm tiềm năng", icon=":material/emoji_events:"),
    ],
    "Sản xuất": [
        st.Page("app_pages/content.py", title="Viết nội dung", icon=":material/edit_note:"),
        st.Page("app_pages/video.py", title="Tạo video", icon=":material/movie:"),
        st.Page("app_pages/ready_to_post.py", title="Sẵn sàng đăng", icon=":material/inventory_2:"),
    ],
    "Phân tích & quản lý": [
        st.Page("app_pages/analytics.py", title="Phân tích", icon=":material/analytics:"),
        st.Page("app_pages/assistant.py", title="Trợ lý AI", icon=":material/smart_toy:"),
        st.Page("app_pages/settings.py", title="Cài đặt", icon=":material/settings:"),
    ],
}

with st.sidebar:
    st.title("Affiliate Auto Tool")
    st.caption("Quy trình affiliate cá nhân")
    st.badge("MVP", icon=":material/rocket_launch:", color="blue")

st.navigation(pages, position="sidebar").run()
