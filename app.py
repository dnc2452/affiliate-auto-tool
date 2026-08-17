import os
import glob
import streamlit as st
from PIL import Image
from dotenv import load_dotenv

load_dotenv(override=True)

from modules.script_generator import MultiModelScriptGenerator
from modules.content_strategy import ContentStrategyAI
from modules.voice_generator import VoiceGenerator
from modules.video_creator import VideoCreator

st.set_page_config(
    page_title="Affiliate Studio AI",
    page_icon="🎬",
    layout="wide"
)

st.title("🎬 Affiliate Studio AI")
st.caption(
    "Tự động nghiên cứu sản phẩm, tạo script, voice và video affiliate."
)

script_gen = MultiModelScriptGenerator()
content_ai = ContentStrategyAI()

tab_research, tab_strategy, tab_script_video, tab_analytics, tab_winner, tab_config = st.tabs([
    "🔍 Product Research",
    "🧠 Content Strategy",
    "🎬 Video Creator",
    "📈 Analytics AI",
    "🔥 Winner Products",
    "⚙️ Settings"
])

# ==================================================
# TAB 1
# ==================================================

with tab_research:

    st.header("🔍 Phân tích sản phẩm")

    product_link = st.text_input(
        "Link TikTok Shop / Shopee"
    )

    raw_description = st.text_area(
        "Mô tả sản phẩm",
        height=200
    )

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
# TAB CONTENT STRATEGY
# ==================================================

with tab_strategy:

    st.header("🧠 AI Content Strategy")

    strategy_product = st.text_input(
        "Tên sản phẩm cần xây nội dung",
        key="strategy_product"
    )

    strategy_desc = st.text_area(
        "Mô tả sản phẩm",
        key="strategy_desc",
        height=150
    )

    if st.button("🚀 Tạo chiến lược nội dung"):

        if not strategy_product:
            st.warning("Nhập tên sản phẩm")

        else:

            with st.spinner("AI đang xây chiến lược..."):

                prompt = f"""
Bạn là chuyên gia TikTok Affiliate.

Sản phẩm:
{strategy_product}

Mô tả:
{strategy_desc}

Hãy tạo:

1. 20 ý tưởng video
2. 20 hook viral
3. 10 CTA
4. 10 caption
5. 20 comment seeding
6. Lịch đăng nội dung 30 ngày

Trả lời bằng tiếng Việt.
"""

                result = script_gen._call_gemini(prompt)

                if result:
                    st.markdown(result)
                else:
                    st.error("AI không phản hồi")
# ==================================================
# TAB 2
# ==================================================

with tab_script_video:

    st.header("🎬 Tạo Video Affiliate")

    col_input, col_output = st.columns([1, 1.2])

    with col_input:

        product_title = st.text_input(
            "Tên sản phẩm",
            value="Loa Bluetooth JBL Xtreme 3"
        )

        product_price = st.number_input(
            "Giá bán",
            value=1500000,
            step=50000
        )

        product_desc = st.text_area(
            "Mô tả sản phẩm",
            height=150
        )

        uploaded_images = st.file_uploader(
            "📸 Upload ảnh",
            type=["jpg", "jpeg", "png"],
            accept_multiple_files=True
        )

        uploaded_videos = st.file_uploader(
            "🎥 Upload video",
            type=["mp4", "mov", "avi"],
            accept_multiple_files=True
        )

        btn_generate = st.button(
            "🚀 Tạo Kịch Bản & Video",
            use_container_width=True
        )

    with col_output:

        if btn_generate:

            if not product_title:

                st.error("Nhập tên sản phẩm")

            elif not uploaded_images and not uploaded_videos:

                st.error("Upload ít nhất 1 ảnh hoặc video")

            else:

                os.makedirs("assets/images", exist_ok=True)
                os.makedirs("assets/videos", exist_ok=True)

                # dọn thư mục cũ

                for f in glob.glob("assets/images/*"):
                    try:
                        os.remove(f)
                    except:
                        pass

                for f in glob.glob("assets/videos/*"):
                    try:
                        os.remove(f)
                    except:
                        pass

                saved_image_paths = []
                saved_video_paths = []

                # lưu ảnh

                for idx, file in enumerate(uploaded_images or []):

                    img_path = (
                        f"assets/images/product_{idx}.jpg"
                    )

                    image = Image.open(file)

                    image.convert("RGB").save(img_path)

                    saved_image_paths.append(img_path)

                # lưu video

                for idx, file in enumerate(uploaded_videos or []):

                    ext = file.name.split(".")[-1]

                    video_path = (
                        f"assets/videos/video_{idx}.{ext}"
                    )

                    with open(video_path, "wb") as f:
                        f.write(file.read())

                    saved_video_paths.append(video_path)

                with st.chat_message(
                    "assistant",
                    avatar="🤖"
                ):

                    st.write(
                        f"Đang xử lý: **{product_title}**"
                    )

                    # ===================================
                    # SCRIPT
                    # ===================================

                    with st.spinner(
                        "1️⃣ AI đang viết kịch bản..."
                    ):

                        product_info = {
                            "title": product_title,
                            "price": product_price,
                            "description": product_desc
                        }

                        sample_image = None

                        if saved_image_paths:
                            sample_image = saved_image_paths[0]

                        script = script_gen.generate_script(
                            product_info,
                            sample_image_path=sample_image
                        )

                    if not script:

                        st.error(
                            "Không tạo được script."
                        )

                    else:

                        st.success(
                            f"Model: {script.used_model}"
                        )

                        # ===============================
                        # VOICE
                        # ===============================

                        with st.spinner(
                            "2️⃣ Sinh giọng đọc..."
                        ):

                            voice_gen = VoiceGenerator()

                            audio_file = (
                                voice_gen.text_to_speech(
                                    script.voiceover,
                                    filename="voice.mp3"
                                )
                            )

                        # ===============================
                        # VIDEO
                        # ===============================

                        with st.spinner(
                            "3️⃣ Render video..."
                        ):

                            video_creator = VideoCreator()

                            video_file = (
                                video_creator
                                .create_video_from_images(
                                    image_paths=saved_image_paths,
                                    audio_path=audio_file,
                                    output_filename="final_video.mp4"
                                )
                            )

                        st.session_state[
                            "current_script"
                        ] = script

                        st.session_state[
                            "current_video"
                        ] = video_file

                        if (
                            video_file
                            and os.path.exists(video_file)
                        ):

                            st.video(video_file)

                        st.subheader("Voiceover")

                        st.info(script.voiceover)

# ==================================================
# TAB 3
# ==================================================

with tab_post_link:

    st.header("📌 Caption & Seeding")

    if "current_script" not in st.session_state:

        st.warning(
            "Tạo video trước."
        )

    else:

        script = st.session_state[
            "current_script"
        ]

        aff_link = st.text_input(
            "Link Affiliate",
            value="https://shopee.vn/..."
        )

        col1, col2 = st.columns(2)

        with col1:

            st.subheader("Caption")

            st.code(
                script.caption,
                language="text"
            )

        with col2:

            st.subheader("Seeding")

            for i, cmt in enumerate(
                script.seeding_comments,
                start=1
            ):

                st.text_area(
                    f"Comment {i}",
                    value=f"{cmt}\n{aff_link}",
                    height=80
                )
# ==================================================
# TAB WINNER PRODUCTS
# ==================================================

with tab_winner:

    st.header("🔥 Winner Product Finder")

    st.info(
        "Dùng để phân tích sản phẩm tiềm năng có khả năng ra đơn cao."
    )

    product_title = st.text_input(
        "Tên sản phẩm",
        key="winner_title"
    )

    rating = st.slider(
        "Đánh giá",
        0.0,
        5.0,
        4.8
    )

    sales = st.number_input(
        "Đơn 30 ngày",
        value=1000
    )

    commission = st.number_input(
        "Hoa hồng %",
        value=15
    )

    if st.button("Tính Winner Score"):

        score = (
            rating * 10
            + min(sales / 1000, 1) * 30
            + min(commission / 20, 1) * 30
        )

        st.success(
            f"Winner Score: {score:.1f}/100"
        )
# ==================================================
# TAB 4
# ==================================================

with tab_config:

    st.header("⚙️ API Keys")

    st.info(
        "Hệ thống tự động đọc file .env"
    )