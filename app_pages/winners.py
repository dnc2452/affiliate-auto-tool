import streamlit as st

from app_pages._shared import database, initialize_state, product_label, products_frame
from modules.product_finder import ProductAnalyzer, ProductMetrics

initialize_state()
db = database()
st.title("Winner finder")
st.caption("Scores are explainable. Missing signals reduce confidence rather than being guessed.")
products = db.get_products(limit=200)
if products:
    st.dataframe(products_frame(products), hide_index=True)
    candidate = st.selectbox("Choose a product for production", products, format_func=product_label)
    if st.button("Approve for content", icon=":material/check_circle:", type="primary"):
        st.session_state["selected_product"] = candidate
        db.update_product_status(candidate["id"], "approved")
        st.success(f"Selected: {candidate['title']}")

with st.expander("Score a product manually", icon=":material/calculate:"):
    with st.form("manual_score"):
        title = st.text_input("Product name")
        price = st.number_input("Price (VND)", min_value=0, value=199000)
        rating = st.slider("Rating", 0.0, 5.0, 4.8)
        sales = st.number_input("Sales in 30 days", min_value=0, value=100)
        reviews = st.number_input("Review count", min_value=0, value=20)
        commission = st.number_input("Commission (%)", min_value=0.0, max_value=100.0, value=0.0)
        score = st.form_submit_button("Calculate score")
    if score:
        result = ProductAnalyzer().analyze(ProductMetrics(product_id="manual", title=title or "Manual product", price=price,
            sales_count_30d=sales, rating=rating, review_count=reviews, commission_rate=commission))
        st.metric("Winner score", f"{result['winner_score']}/100")
        st.bar_chart(result["score_breakdown"])
        for note in result["score_caveats"]:
            st.warning(note)
