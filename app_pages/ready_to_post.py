from pathlib import Path

import streamlit as st

from app_pages._shared import database, initialize_state, product_label
from modules.package_manager import ReadyToPostManager

initialize_state()
db = database()
st.title("Sẵn sàng đăng bài")
st.caption("Đây là bàn xuất bản: copy nội dung, tải media và mở đúng link sản phẩm để đăng thủ công trên nền tảng.")
product = st.session_state.get("selected_product")
content = st.session_state.get("latest_content")
media = st.session_state.get("latest_media") or {}
if product:
    st.write(f"Product: **{product_label(product)}**")
if not product or not content:
    st.info("Chọn một sản phẩm và tạo content trước. Sau đó mọi thứ cần để đăng sẽ hiện ở đây.", icon=":material/inventory_2:")
    st.stop()

st.subheader("Nội dung để đăng")
st.text_area("Caption — copy và dán vào TikTok/Shopee/Lazada", content.get("caption", ""), height=110, key="post_caption")
st.text_area("Voiceover", content.get("voiceover", ""), height=180, key="post_voiceover")
st.text_input("Hashtags", content.get("hashtags", ""), key="post_hashtags")
st.text_area("Seeding comments", "\n".join(content.get("seeding_comments", [])), height=120, key="post_comments")

with st.container(horizontal=True):
    st.download_button("Tải caption", content.get("caption", "").encode("utf-8"), "caption.txt", "text/plain", icon=":material/download:")
    st.download_button("Tải voiceover", content.get("voiceover", "").encode("utf-8"), "voiceover.txt", "text/plain", icon=":material/download:")
    st.download_button("Tải hashtags", content.get("hashtags", "").encode("utf-8"), "hashtags.txt", "text/plain", icon=":material/download:")

link = product.get("affiliate_url") or product.get("product_url")
if link:
    st.link_button("Mở link sản phẩm / affiliate", link, icon=":material/open_in_new:", type="primary")
else:
    st.warning("Sản phẩm này chưa có link. Hãy quay lại Product research để dán link trực tiếp hoặc import CSV affiliate.")

st.subheader("Media để đăng")
has_media = False
for label, path_key, filename, mime in (
    ("Video dọc", "video_path", "affiliate-video.mp4", "video/mp4"),
    ("Audio voiceover", "audio_path", "voiceover.mp3", "audio/mpeg"),
    ("Thumbnail", "thumbnail_path", "thumbnail.jpg", "image/jpeg"),
):
    path = Path(media.get(path_key, "")) if media.get(path_key) else None
    if path and path.is_file():
        has_media = True
        st.write(f"**{label}**")
        if mime == "video/mp4":
            st.video(str(path))
        elif mime == "audio/mpeg":
            st.audio(str(path))
        else:
            st.image(str(path), width=220)
        st.download_button(f"Tải {label.lower()}", path.read_bytes(), filename, mime, icon=":material/download:")
if not has_media:
    st.info("Chưa có media. Vào Video studio để render video, hoặc vẫn có thể dùng caption/voiceover để dựng bằng công cụ bên ngoài.", icon=":material/movie:")

with st.expander("Lưu package để backup", icon=":material/archive:"):
    st.caption("Package chỉ là bản sao lưu nội bộ. Đăng bài trực tiếp bằng các nút copy/tải ở trên; không cần dùng đường dẫn kỹ thuật.")
    if st.button("Tạo bản backup", icon=":material/archive:"):
        result = ReadyToPostManager().create(product, content, media)
        package_id = db.save_ready_package(product["id"], result["package_path"], result["manifest_path"])
        db.update_product_status(product["id"], "packaged")
        st.session_state["latest_package"] = result
        st.success(f"Đã tạo bản backup #{package_id}.")

packages = db.get_ready_packages(limit=5)
if packages:
    st.caption(f"Đã lưu {len(packages)} package gần đây. Trên Streamlit Cloud, file backup có thể mất sau khi server khởi động lại; hãy tải media ngay từ màn hình này.")
