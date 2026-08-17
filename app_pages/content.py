import streamlit as st

from agents.content_agent import ContentAgent
from app_pages._shared import content_language_label, database, initialize_state, parse_comments, product_label, save_upload

initialize_state()
db = database()
st.title("Content studio")
language = st.session_state["content_language"]
st.caption(f"Create an original, platform-native script in {content_language_label(language)}. Review all claims before publishing.")
products = db.get_products(limit=100)
selected = st.session_state.get("selected_product")
if products:
    index = next((i for i, product in enumerate(products) if selected and product["id"] == selected.get("id")), 0)
    selected = st.selectbox("Product", products, index=index, format_func=product_label)
    st.session_state["selected_product"] = selected
    image = st.file_uploader("Optional product image", type=["jpg", "jpeg", "png"])
    if st.button("Generate content", icon=":material/auto_awesome:", type="primary"):
        image_path = None
        if image:
            from pathlib import Path
            image_path = save_upload(image, Path("data") / "uploads", "content")
        with st.status("Generating content…", expanded=True) as status:
            content = ContentAgent().run(selected, image_path=image_path, language=language)
            status.update(label="Content generated" if content else "Generation failed", state="complete")
        if content:
            st.session_state["latest_content"] = content
if st.session_state.get("latest_content"):
    content = st.session_state["latest_content"]
    st.subheader("Current draft")
    voiceover = st.text_area("Voiceover", content["voiceover"], height=200, key="content_voiceover")
    caption = st.text_area("Caption", content["caption"], height=100, key="content_caption")
    hook = st.text_input("Hook", content.get("hook", ""), key="content_hook")
    hashtags = st.text_input("Hashtags", content.get("hashtags", ""), key="content_hashtags")
    comments = st.text_area("Seeding comments (one per line)", "\n".join(content.get("seeding_comments", [])), key="content_comments")
    if st.button("Save reviewed draft", icon=":material/save:"):
        content.update(voiceover=voiceover, caption=caption, hook=hook, hashtags=hashtags,
                       seeding_comments=parse_comments(comments))
        if content.get("content_id"):
            db.update_content(int(content["content_id"]), content)
        st.session_state["latest_content"] = content
        st.success("Reviewed draft saved for video and packaging.")
else:
    st.info("Choose a winner product first.", icon=":material/emoji_events:")
