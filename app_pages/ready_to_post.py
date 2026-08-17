import streamlit as st

from app_pages._shared import database, initialize_state, product_label
from modules.package_manager import ReadyToPostManager

initialize_state()
db = database()
st.title("Ready to post")
st.caption("Export one portable folder containing the approved post assets and disclosure guidance.")
product = st.session_state.get("selected_product")
content = st.session_state.get("latest_content")
media = st.session_state.get("latest_media") or {}
if product:
    st.write(f"Product: **{product_label(product)}**")
if not product or not content:
    st.info("Approve a product and generate content before making a package.", icon=":material/inventory_2:")
elif st.button("Create package", icon=":material/archive:", type="primary"):
    result = ReadyToPostManager().create(product, content, media)
    package_id = db.save_ready_package(product["id"], result["package_path"], result["manifest_path"])
    db.update_product_status(product["id"], "packaged")
    st.success(f"Package #{package_id} created.")
    st.code(result["package_path"], language="text")
    st.caption("Check all product claims, affiliate link and platform disclosure before publishing.")

packages = db.get_ready_packages(limit=20)
if packages:
    st.subheader("Recent packages")
    st.dataframe(packages, hide_index=True, column_config={"package_path": None, "manifest_path": None})
