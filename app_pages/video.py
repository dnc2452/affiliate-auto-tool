import streamlit as st

from agents.video_agent import VideoAgent
from app_pages._shared import initialize_state, save_upload

initialize_state()
st.title("Video studio")
st.caption("FFmpeg is used first for a portable 9:16 render. Only upload media you own or are licensed to use.")
content = st.session_state.get("latest_content")
uploads = st.file_uploader("Product images", type=["jpg", "jpeg", "png"], accept_multiple_files=True)
if content and uploads and st.button("Render vertical video", icon=":material/movie:", type="primary"):
    from pathlib import Path
    paths = []
    for upload in uploads:
        paths.append(save_upload(upload, Path("data") / "uploads", "video"))
    with st.status("Rendering video…", expanded=True) as status:
        media = VideoAgent().run(content, image_paths=paths)
        status.update(label="Video ready" if media and media.get("video_path") else "Audio created; video could not render", state="complete")
    if media:
        st.session_state["latest_media"] = media
if st.session_state.get("latest_media"):
    media = st.session_state["latest_media"]
    if media.get("video_path"):
        st.video(media["video_path"])
    if media.get("audio_path"):
        st.audio(media["audio_path"])
elif not content:
    st.info("Generate content first, then return here to render.", icon=":material/edit_note:")
