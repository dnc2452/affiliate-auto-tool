import streamlit as st

from app_pages._shared import database, initialize_state, products_frame
from modules.analytics_service import build_summary, generate_insights

initialize_state()
db = database()
products = db.get_products(limit=200)
summary = build_summary(db.get_analytics_records())
totals = summary["totals"]

st.title("Command center")
st.caption("Research → approve → content → video → package → analytics → optimize")
with st.container(horizontal=True):
    st.metric("Products researched", len(products), border=True)
    st.metric("Winner candidates", sum(item.get("winner_score", 0) >= 60 for item in products), border=True)
    st.metric("Orders", f"{totals['orders']:,.0f}", border=True)
    st.metric("Commission", f"{totals['commission']:,.0f}đ", border=True)

left, right = st.columns(2)
with left:
    with st.container(border=True):
        st.subheader("Top product opportunities")
        if products:
            st.dataframe(products_frame(products[:8]), hide_index=True)
        else:
            st.info("Chưa có sản phẩm. Bắt đầu ở Product research.", icon=":material/travel_explore:")
with right:
    with st.container(border=True):
        st.subheader("Next best actions")
        for insight in generate_insights(summary):
            st.write(f":material/arrow_forward: {insight}")
