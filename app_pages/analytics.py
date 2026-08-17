import pandas as pd
import streamlit as st

from app_pages._shared import database
from modules.analytics_service import build_summary, generate_insights, parse_analytics_csv

db = database()
st.title("Analytics")
st.caption("Import reports repeatedly. Duplicate rows are ignored and historical data is preserved.")
platform = st.segmented_control("Source platform", ["shopee", "tiktok", "lazada"], default="shopee")
file = st.file_uploader("Analytics CSV export", type="csv")
if file and st.button("Import analytics", icon=":material/upload:", type="primary"):
    try:
        records = parse_analytics_csv(file.getvalue(), platform)
        count = db.import_analytics(records, platform, file.name)
        st.success(f"Imported {count} new rows; duplicate rows were skipped.")
    except ValueError as error:
        st.error(str(error))
records = db.get_analytics_records()
summary = build_summary(records)
totals = summary["totals"]
with st.container(horizontal=True):
    st.metric("Revenue", f"{totals['revenue']:,.0f}đ", border=True)
    st.metric("Orders", f"{totals['orders']:,.0f}", border=True)
    st.metric("Conversion", f"{totals['conversion_rate']:.2f}%", border=True)
    st.metric("Commission", f"{totals['commission']:,.0f}đ", border=True)
if totals["roi"] is not None:
    st.metric("ROI", f"{totals['roi']:.1f}%", border=True)
if summary["products"]:
    products = pd.DataFrame(summary["products"])
    left, right = st.columns(2)
    with left:
        st.subheader("Commission by product")
        st.bar_chart(products, x="product_name", y="commission")
    with right:
        st.subheader("AI-style action list")
        for insight in generate_insights(summary):
            st.write(f":material/arrow_forward: {insight}")
if records:
    history = pd.DataFrame(records)
    if "record_date" in history and history["record_date"].notna().any():
        trend = history.groupby("record_date", as_index=False)[["revenue", "commission", "orders"]].sum()
        with st.container(border=True):
            st.subheader("Performance over time")
            st.line_chart(trend, x="record_date", y=["revenue", "commission"])
    st.subheader("Historical records")
    st.dataframe(history, hide_index=True)
