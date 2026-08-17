import os
import glob
import streamlit as st
from PIL import Image
from dotenv import load_dotenv
from pathlib import Path

load_dotenv(override=True)

from modules.script_generator import MultiModelScriptGenerator
from modules.voice_generator import VoiceGenerator
from modules.video_creator import VideoCreator

# Import Agent mới
from agents.research_agent import ResearchAgent
from agents.content_agent import ContentAgent
from agents.video_agent import VideoAgent
from agents.pipeline import AffiliatePipeline

st.set_page_config(
    page_title="Affiliate Studio AI",
    page_icon="🎬",
    layout="wide"
)

st.title("🎬 Affiliate Studio AI")
st.caption("Tự động nghiên cứu sản phẩm → viết kịch bản → tạo voice → render video affiliate")

# Khởi tạo
script_gen = MultiModelScriptGenerator()
pipeline = AffiliatePipeline()

tab_pipeline, tab_research, tab_script_video, tab_winner, tab_config = st.tabs([
    "🚀 Auto Pipeline",
    "🔍 Product Research",
    "🎬 Video Creator (Thủ công)",
    "🔥 Winner Products",
    "⚙️ Settings"
])

# ==================================================
# TAB 1: AUTO PIPELINE (MỚI - QUAN TRỌNG NHẤT)
# ==================================================
with tab_pipeline:
    st.header("🚀 Auto Pipeline – Chạy tự động toàn bộ")
    st.info("Quy trình: Tìm sản phẩm → Chấm điểm → Viết kịch bản → Tạo audio/video")

    col1, col2 = st.columns([1, 1])

    with col1:
        keyword = st.text_input("Từ khóa sản phẩm", value="dầu gội phủ bạc")
        platform = st.selectbox("Sàn", ["shopee", "tiktok", "lazada"], index=0)
        limit = st.slider("Số sản phẩm muốn lấy", 1, 10, 2)
        min_score = st.slider("Điểm Winner tối thiểu", 40, 90, 60)

    with col2:
        st.write("**Ảnh sản phẩm (để render video)**")
        uploaded_images = st.file_uploader(
            "Upload ảnh (có thể chọn nhiều)",
            type=["jpg", "jpeg", "png"],
            accept_multiple_files=True,
            key="pipeline_images"
        )

        use_demo = st.checkbox("Dùng dữ liệu demo (khi chưa có sản phẩm thật)", value=True)

    if st.button("🚀 Chạy Auto Pipeline", type="primary", use_container_width=True):

        # Lưu ảnh tạm
        image_paths = []
        if uploaded_images:
            os.makedirs("assets/images", exist_ok=True)
            for f in glob.glob("assets/images/*"):
                try:
                    os.remove(f)
                except:
                    pass

            for idx, file in enumerate(uploaded_images):
                img_path = f"assets/images/pipeline_{idx}.jpg"
                Image.open(file).convert("RGB").save(img_path)
                image_paths.append(img_path)

        with st.spinner("Đang chạy toàn bộ pipeline..."):
            results = pipeline.run(
                keyword=keyword if use_demo else keyword,
                platform=platform,
                limit=limit,
                min_score=min_score,
                image_paths=image_paths if image_paths else None
            )

        if not results:
            st.warning("Không có kết quả nào được tạo.")
        else:
            st.success(f"Hoàn thành {len(results)} sản phẩm!")

            for i, item in enumerate(results, 1):
                product = item["product"]
                content = item["content"]
                media = item.get("media") or {}

                with st.expander(f"#{i} | {product.get('title')} | Score: {product.get('winner_score')}", expanded=(i == 1)):
                    st.write(f"**Platform:** {product.get('platform')} | **Giá:** {product.get('price'):,.0f}đ")
                    st.write(f"**Model dùng:** {content.get('used_model')}")

                    st.subheader("Voiceover")
                    st.info(content.get("voiceover"))

                    st.subheader("Caption")
                    st.code(content.get("caption"), language="text")

                    st.subheader("Seeding Comments")
                    for cmt in content.get("seeding_comments", []):
                        st.write(f"- {cmt}")

                    if media.get("audio_path"):
                        st.audio(media["audio_path"])

                    if media.get("video_path") and os.path.exists(media["video_path"]):
                        st.video(media["video_path"])
                    elif image_paths:
                        st.warning("Video chưa được tạo (có thể do lỗi render).")
                    else:
                        st.info("Chưa upload ảnh → chỉ tạo audio.")

# ==================================================
# TAB 2: PRODUCT RESEARCH (giữ lại)
# ==================================================
with tab_research:
    st.header("🔍 Phân tích sản phẩm")

    product_link = st.text_input("Link TikTok Shop / Shopee")
    raw_description = st.text_area("Mô tả sản phẩm", height=200)

    if st.button("🔎 AI Phân Tích"):
        if not product_link and not raw_description:
            st.warning("Vui lòng nhập dữ liệu.")
        else:
            with st.spinner("AI đang phân tích..."):
                prompt = f"""
Phân tích sản phẩm sau:

Link:
{product_link}

Mô tả:
{raw_description}

Trả về:

1. Khách hàng mục tiêu
2. USP
3. 3 Hook video mạnh nhất
"""
                result = script_gen._call_gemini(prompt)
                if result:
                    st.success("Hoàn tất")
                    st.markdown(result)
                else:
                    st.error("Không gọi được Gemini")

# ==================================================
# TAB 3: VIDEO CREATOR THỦ CÔNG (giữ lại)
# ==================================================
with tab_script_video:
    st.header("🎬 Tạo Video Affiliate (Thủ công)")

    col_input, col_output = st.columns([1, 1.2])

    with col_input:
        product_title = st.text_input("Tên sản phẩm", value="Loa Bluetooth JBL Xtreme 3")
        product_price = st.number_input("Giá bán", value=1500000, step=50000)
        product_desc = st.text_area("Mô tả sản phẩm", height=150)

        uploaded_images_manual = st.file_uploader(
            "📸 Upload ảnh",
            type=["jpg", "jpeg", "png"],
            accept_multiple_files=True,
            key="manual_images"
        )

        btn_generate = st.button("🚀 Tạo Kịch Bản & Video", use_container_width=True)

    with col_output:
        if btn_generate:
            if not product_title:
                st.error("Nhập tên sản phẩm")
            elif not uploaded_images_manual:
                st.error("Upload ít nhất 1 ảnh")
            else:
                os.makedirs("assets/images", exist_ok=True)
                for f in glob.glob("assets/images/*"):
                    try:
                        os.remove(f)
                    except:
                        pass

                saved_image_paths = []
                for idx, file in enumerate(uploaded_images_manual):
                    img_path = f"assets/images/product_{idx}.jpg"
                    Image.open(file).convert("RGB").save(img_path)
                    saved_image_paths.append(img_path)

                with st.spinner("1️⃣ AI đang viết kịch bản..."):
                    product_info = {
                        "title": product_title,
                        "price": product_price,
                        "description": product_desc
                    }
                    script = script_gen.generate_script(
                        product_info,
                        sample_image_path=saved_image_paths[0] if saved_image_paths else None
                    )

                if not script:
                    st.error("Không tạo được script.")
                else:
                    st.success(f"Model: {script.used_model}")

                    with st.spinner("2️⃣ Sinh giọng đọc..."):
                        voice_gen = VoiceGenerator()
                        audio_file = voice_gen.text_to_speech(script.voiceover, filename="voice.mp3")

                    with st.spinner("3️⃣ Render video..."):
                        video_creator = VideoCreator()
                        video_file = video_creator.create_video_from_images(
                            image_paths=saved_image_paths,
                            audio_path=audio_file,
                            output_filename="final_video.mp4"
                        )

                    st.session_state["current_script"] = script
                    st.session_state["current_video"] = video_file

                    if video_file and os.path.exists(video_file):
                        st.video(video_file)

                    st.subheader("Voiceover")
                    st.info(script.voiceover)

                    st.subheader("Caption")
                    st.code(script.caption, language="text")

                    st.subheader("Seeding Comments")
                    for cmt in script.seeding_comments:
                        st.write(f"- {cmt}")

# ==================================================
# TAB 4: WINNER PRODUCTS
# ==================================================
with tab_winner:
    st.header("🔥 Winner Product Finder")

    product_title = st.text_input("Tên sản phẩm", key="winner_title")
    rating = st.slider("Đánh giá", 0.0, 5.0, 4.8)
    sales = st.number_input("Đơn 30 ngày", value=1000)
    commission = st.number_input("Hoa hồng %", value=15)

    if st.button("Tính Winner Score"):
        score = (
            rating * 10
            + min(sales / 1000, 1) * 30
            + min(commission / 20, 1) * 30
        )
        st.success(f"Winner Score: {score:.1f}/100")

# ==================================================
# TAB 5: SETTINGS
# ==================================================
with tab_config:
    st.header("⚙️ API Keys & Cấu hình")
    st.info("Hệ thống tự động đọc file `.env`. Bạn chỉ cần điền key vào file đó.")

    st.markdown("""
    **Các key đang hỗ trợ (free-first):**
    - `GEMINI_API_KEY`
    - `GROQ_API_KEY`
    - `OPENROUTER_API_KEY`
    - `OPENAI_API_KEY`
    - `AIMLAPI_KEY`
    - `CEREBRAS_API_KEY`
    - `NVIDIA_API_KEY`
    """)

    st.success("Khuyến nghị dùng Gemini hoặc Groq để bắt đầu (miễn phí).")