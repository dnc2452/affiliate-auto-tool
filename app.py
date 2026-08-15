import os
import glob
import streamlit as st
from PIL import Image
from dotenv import load_dotenv

# Nạp biến môi trường ngay lập tức khi ứng dụng khởi chạy
load_dotenv(override=True)

from modules.script_generator import MultiModelScriptGenerator
from modules.voice_generator import VoiceGenerator
from modules.video_creator import VideoCreator

# Cấu hình trang
st.set_page_config(
    page_title="Affiliate Studio AI",
    page_icon="🎬",
    layout="wide"
)

st.title("🎬 Affiliate Studio AI - Tự Động Hóa Kịch Bản & Render Video")
st.caption("Hệ thống hỗ trợ Creator/Affiliater nghiên cứu sản phẩm, tạo kịch bản, render video 9:16 và seeding bán hàng.")

# TAB SYSTEM
tab_research, tab_script_video, tab_post_link, tab_config = st.tabs([
    "🔍 1. Nghiên Cứu Sản Phẩm Affiliate",
    "🎬 2. Viết Kịch Bản & Render Video/Ảnh",
    "📌 3. Viết Caption & Seeding Link Affiliate",
    "⚙️ 4. Cấu Hình & API Keys"
])

# Khởi tạo Script Generator Engine
script_gen = MultiModelScriptGenerator()

# ==========================================
# TAB 1: NGHIÊN CỨU SẢN PHẨM AFFILIATE (THỰC TẾ)
# ==========================================
with tab_research:
    st.header("🔍 Phân Tích & Nghiên Cứu Sản Phẩm")
    st.write("Nhập thông tin hoặc dán link sàn (TikTok Shop / Shopee) để AI bóc tách USP và tệp khách hàng mục tiêu.")
    
    col_r1, col_r2 = st.columns([1, 1])
    with col_r1:
        product_link = st.text_input("🔗 Link sản phẩm Affiliate (Shopee / TikTok Shop):", key="aff_link_tab1")
        raw_description = st.text_area(
            "📝 Mô tả / Đặc tính sản phẩm (Copy toàn bộ tên/mô tả trên sàn vào đây):", 
            height=180, 
            placeholder="Ví dụ: Loa Bluetooth JBL Xtreme 3 - Siêu Âm Bass Nghe Nhạc Hay..."
        )
        btn_analyze = st.button("🔎 AI Phân Tích USP & Persona", type="primary")

    with col_r2:
        if btn_analyze:
            if not raw_description and not product_link:
                st.warning("⚠️ Vui lòng nhập thông tin mô tả sản phẩm hoặc dán link!")
            else:
                with st.spinner("🤖 AI đang phân tích dữ liệu sản phẩm mới..."):
                    input_text = f"Link: {product_link}\nMô tả chi tiết: {raw_description}"
                    analysis_result = script_gen._call_gemini(f"""
Hãy đóng vai chuyên gia Marketing Affiliate. Hãy phân tích sản phẩm sau đây:
{input_text}

Trả về kết quả ngắn gọn theo 3 mục bằng Tiếng Việt:
1. Tệp khách hàng mục tiêu (Độ tuổi, sở thích, nhu cầu)
2. USP (Điểm bán hàng độc nhất / Tính năng nổi bật nhất)
3. 3 Góc quay/Hook hấp dẫn nhất để làm video ngắn (TikTok/Reels)
""")
                    if analysis_result:
                        st.success("🎯 Kết quả phân tích sản phẩm thực tế:")
                        st.markdown(analysis_result)
                    else:
                        st.error("Không thể kết nối AI. Vui lòng kiểm tra lại GEMINI_API_KEY trong file .env!")
        else:
            st.info("💡 Nhập mô tả sản phẩm ở cột bên trái và nhấn nút phân tích.")

# ==========================================
# TAB 2: VIẾT KỊCH BẢN & RENDER VIDEO/ẢNH
# ==========================================
with tab_script_video:
    st.header("🎬 Viết Kịch Bản & Tạo Video / Ảnh Affiliate")
    
    col_input, col_output = st.columns([1, 1.2])

    with col_input:
        st.subheader("📦 Thông tin sản phẩm mới")
        product_title = st.text_input("Tên sản phẩm:", value="Loa Bluetooth JBL Xtreme 3", key="title_tab2")
        product_price = st.number_input("Giá bán (VNĐ):", value=1500000, step=50000, key="price_tab2")
        
        product_desc = st.text_area(
            "Mô tả chi tiết sản phẩm:", 
            value="Loa bluetooth công suất lớn, âm bass trầm ấm chống nước chuẩn IP67, pin trâu 15 giờ liên tục, tích hợp quai đeo tiện lợi đi du lịch.",
            height=120,
            key="desc_tab2"
        )

        uploaded_files = st.file_uploader(
            "Tải lên ảnh sản phẩm mới (PNG, JPG):", 
            type=["png", "jpg", "jpeg"], 
            accept_multiple_files=True,
            key="files_tab2"
        )

        btn_generate = st.button("🚀 Bắt đầu Tạo Kịch Bản & Render Video", type="primary", use_container_width=True)

    with col_output:
        st.subheader("🎉 Kết quả xử lý AI")

        if btn_generate:
            if not product_title:
                st.error("⚠️ Vui lòng nhập tên sản phẩm!")
            elif not uploaded_files:
                st.error("⚠️ Vui lòng tải lên ít nhất 1 hình ảnh sản phẩm!")
            else:
                os.makedirs("assets/images", exist_ok=True)
                old_files = glob.glob("assets/images/*")
                for f in old_files:
                    try:
                        os.remove(f)
                    except Exception:
                        pass
                
                saved_image_paths = []
                for idx, uploaded_file in enumerate(uploaded_files):
                    img_path = f"assets/images/product_img_{idx}.jpg"
                    image = Image.open(uploaded_file)
                    image.convert("RGB").save(img_path)
                    saved_image_paths.append(img_path)

                with st.chat_message("assistant", avatar="🤖"):
                    st.write(f"Đang xử lý sản phẩm: **{product_title}**")

                    with st.spinner("1️⃣ AI đang đọc mô tả và hình ảnh mới để viết kịch bản..."):
                        product_info = {
                            "title": product_title, 
                            "price": product_price,
                            "description": product_desc
                        }
                        script = script_gen.generate_script(product_info, sample_image_path=saved_image_paths[0])

                    if script:
                        st.success(f"Tạo kịch bản thành công bằng Engine: **{script.used_model}**")

                        with st.spinner("2️⃣ Đang tạo file audio giọng đọc MP3..."):
                            voice_gen = VoiceGenerator()
                            audio_file = voice_gen.text_to_speech(script.voiceover, filename="voiceover_main.mp3")

                        with st.spinner("3️⃣ Đang dựng và render Video 9:16..."):
                            video_gen = VideoCreator()
                            video_file = video_gen.create_video_from_images(
                                image_paths=saved_image_paths,
                                audio_path=audio_file,
                                output_filename="web_final_video.mp4"
                            )

                        st.session_state['current_script'] = script
                        st.session_state['current_video'] = video_file

                        st.markdown("---")
                        if video_file and os.path.exists(video_file):
                            st.markdown("**🎬 Video Render hoàn chỉnh:**")
                            st.video(video_file)

                        st.markdown("**🔊 Lời đọc Voiceover:**")
                        st.info(script.voiceover)
                    else:
                        st.error("Không thể tạo kịch bản. Vui lòng kiểm tra lại các API Key trong file .env!")

# ==========================================
# TAB 3: CAPTION & SEEDING
# ==========================================
with tab_post_link:
    st.header("📌 Quản Lý Bài Đăng & Seeding Link Affiliate")
    if 'current_script' in st.session_state:
        script = st.session_state['current_script']
        default_link = st.session_state.get('aff_link_tab1', 'https://shopee.vn/...')
        
        col_c1, col_c2 = st.columns([1, 1])
        with col_c1:
            st.subheader("📝 Caption & Hashtags Đăng Bài")
            st.code(script.caption, language="text")
            st.markdown("---")
            aff_link = st.text_input("Dán link Affiliate của bạn:", value=default_link if default_link else "https://shopee.vn/...")
        with col_c2:
            st.subheader("💬 Kịch Bản Seeding Comments Mồi")
            for idx, cmt in enumerate(script.seeding_comments, start=1):
                st.text_area(f"Bình luận #{idx}:", value=f"{cmt} (Link mua ở đây nè: {aff_link})", height=70)
    else:
        st.warning("⚠️ Chưa có dữ liệu. Vui lòng tạo video ở Tab 2 trước.")

# ==========================================
# TAB 4: CẤU HÌNH API
# ==========================================
with tab_config:
    st.header("⚙️ Cấu Hình API Keys")
    st.info("Hệ thống tự động sử dụng file `.env` để lấy API Keys.")