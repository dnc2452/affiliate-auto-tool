import os
import shutil

import streamlit as st

from app_pages._shared import content_language_label, initialize_state
from core.config import DATA_DIR, OUTPUT_DIR

initialize_state()
st.title("Settings")
st.caption("Secrets stay outside Git. Add API keys to a local .env file or Streamlit secrets in deployment.")
keys = ["GEMINI_API_KEY", "GROQ_API_KEY", "OPENROUTER_API_KEY", "OPENAI_API_KEY", "CEREBRAS_API_KEY", "NVIDIA_API_KEY"]
for key in keys:
    st.badge(f"{key}: {'configured' if os.getenv(key) else 'not configured'}", icon=":material/key:", color="green" if os.getenv(key) else "gray")
st.subheader("Content language")
language = st.segmented_control(
    "Language for newly generated scripts",
    options=["vi", "en"],
    format_func=content_language_label,
    key="content_language",
)
st.caption(f"Current default: {content_language_label(language or 'vi')}. This changes AI-generated voiceover, captions and comments; it does not translate existing drafts.")
st.subheader("Runtime checks")
st.write(f"Data folder: `{DATA_DIR}`")
st.write(f"Output folder: `{OUTPUT_DIR}`")
st.write(f"FFmpeg: {'available' if shutil.which('ffmpeg') else 'bundled renderer fallback available'}")
st.info("For Streamlit Community Cloud, set each key in App settings → Secrets. SQLite is suitable for a personal MVP; move to Postgres before multi-user SaaS.", icon=":material/info:")
