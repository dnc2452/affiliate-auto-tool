import streamlit as st

from agents.research_agent import ResearchAgent
from app_pages._shared import initialize_state, products_frame
from modules.product_importer import ProductImportError, import_products_csv

initialize_state()
st.title("Product research")
st.caption("Use public marketplace data when available, or import an approved affiliate export for verified sales and commission.")

with st.form("research_form"):
    keyword = st.text_input("Product keyword", placeholder="Example: smart home sensor light")
    platform = st.segmented_control("Platform", ["shopee", "tiktok", "lazada"], default="shopee")
    limit = st.slider("Maximum products", 1, 30, 10)
    submitted = st.form_submit_button("Research public products", icon=":material/search:", type="primary")
if submitted:
    try:
        with st.status("Researching public product data…", expanded=True) as status:
            results = ResearchAgent().run(keyword=keyword, platform=platform, limit=limit, min_score=0)
            status.update(label="Research complete" if results else "No public results available", state="complete")
        if results:
            st.session_state["research_results"] = results
            st.dataframe(products_frame(results), hide_index=True)
        else:
            st.warning("No usable public result. Import a CSV export from the affiliate portal instead; the app will not invent commission data.")
    except ValueError as error:
        st.error(str(error))

st.subheader("Import verified affiliate CSV")
csv_file = st.file_uploader("Affiliate CSV export", type="csv")
if csv_file and st.button("Import and score", icon=":material/upload:"):
    try:
        records = import_products_csv(csv_file.getvalue(), platform)
        results = ResearchAgent().run(products=records, platform=platform, limit=len(records), min_score=0)
        st.session_state["research_results"] = results
        st.success(f"Imported and scored {len(results)} products.")
        st.dataframe(products_frame(results), hide_index=True)
    except ProductImportError as error:
        st.error(str(error))
