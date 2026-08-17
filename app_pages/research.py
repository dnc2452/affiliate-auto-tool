import streamlit as st

from agents.research_agent import ResearchAgent
from app_pages._shared import initialize_state, products_frame
from modules.product_importer import ProductImportError, import_products_csv


def show_results(results):
    st.dataframe(
        products_frame(results),
        hide_index=True,
        column_config={
            "product_url": st.column_config.LinkColumn("Product link", display_text="Open product"),
            "winner_score": st.column_config.NumberColumn("Winner score", format="%.1f / 100"),
            "score_confidence": st.column_config.NumberColumn("Data confidence", format="%.0f%%"),
        },
    )
    for product in results:
        with st.expander(product.get("title", "Product")):
            if product.get("product_url"):
                st.link_button("Open the exact product page", product["product_url"], icon=":material/open_in_new:")
            if product.get("affiliate_url"):
                st.link_button("Open verified affiliate link", product["affiliate_url"], icon=":material/link:")
            for caveat in product.get("score_caveats", []):
                st.warning(caveat)


initialize_state()
st.title("Nghiên cứu sản phẩm")
st.caption("Dán link sản phẩm để AI bám đúng sản phẩm đó; hoặc tìm công khai và import CSV affiliate đã xác minh.")

with st.form("research_form", border=True):
    product_url = st.text_input(
        "Link sản phẩm / affiliate (ưu tiên)",
        placeholder="https://shopee.vn/... hoặc link TikTok Shop/Lazada",
        help="Khi có link, hệ thống chỉ đọc trang công khai của chính sản phẩm đó. Không tự tạo giá, hoa hồng hay affiliate link.",
    )
    keyword = st.text_input("Từ khóa sản phẩm", placeholder="Ví dụ: đèn cảm biến thông minh")
    platform = st.segmented_control("Nền tảng", ["shopee", "tiktok", "lazada"], default="shopee")
    limit = st.slider("Số sản phẩm tối đa khi tìm bằng từ khóa", 1, 30, 10)
    submitted = st.form_submit_button("Nghiên cứu sản phẩm", icon=":material/search:", type="primary")
if submitted:
    try:
        with st.status("Đang đọc dữ liệu sản phẩm công khai…", expanded=True) as status:
            results = ResearchAgent().run(keyword=keyword, product_url=product_url, platform=platform, limit=limit, min_score=0)
            status.update(label="Đã hoàn tất" if results else "Chưa lấy được dữ liệu", state="complete")
        if results:
            st.session_state["research_results"] = results
            show_results(results)
        else:
            st.warning("Không lấy được dữ liệu công khai. Hãy dùng link sản phẩm đầy đủ hoặc import CSV từ affiliate portal.")
    except ValueError as error:
        st.error(str(error))

st.subheader("Import CSV affiliate đã xác minh")
st.caption("Dùng export từ affiliate portal khi bạn cần đúng hoa hồng, doanh số hoặc affiliate link.")
csv_file = st.file_uploader("Affiliate CSV export", type="csv")
if csv_file and st.button("Import và chấm điểm", icon=":material/upload:"):
    try:
        records = import_products_csv(csv_file.getvalue(), platform)
        results = ResearchAgent().run(products=records, platform=platform, limit=len(records), min_score=0)
        st.session_state["research_results"] = results
        st.success(f"Đã import và chấm điểm {len(results)} sản phẩm.")
        show_results(results)
    except ProductImportError as error:
        st.error(str(error))
