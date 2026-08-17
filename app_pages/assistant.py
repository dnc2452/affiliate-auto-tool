import streamlit as st

from agents.assistant_router import AffiliateAssistant
from app_pages._shared import database

db = database()
assistant = AffiliateAssistant(db)
st.title("Affiliate AI assistant")
st.caption("Ask about winner products, analytics performance, or new content concepts.")
for message in db.get_assistant_messages():
    with st.chat_message(message["role"]):
        st.write(message["message"])
prompt = st.chat_input("Example: Why did product A have low conversion?")
if prompt:
    with st.chat_message("user"):
        st.write(prompt)
    with st.chat_message("assistant"):
        with st.spinner("Routing request…"):
            result = assistant.respond(prompt)
        st.write(result["answer"])
        st.caption(f"Routed to: {result['route']}")
