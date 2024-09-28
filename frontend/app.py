import os

import streamlit as st
import requests
from dotenv import load_dotenv

load_dotenv()
API_URL = os.getenv("API_URL")

if "messages" not in st.session_state:
    st.session_state.messages = []

st.sidebar.title("Chat Settings")
user_id = st.sidebar.text_input("User ID", value="user_123")
conversation_id = st.sidebar.text_input("Conversation ID", value="conv_123")

def send_message(user_message, user_id, conversation_id):
    payload = {
        "user_message": user_message,
        "user_id": user_id,
        "conversation_id": conversation_id
    }
    response = requests.post(f"{API_URL}/chat/completions", json=payload)
    
    if response.status_code == 200:
        return response.json()["data"]["content"]
    else:
        return "Error: Could not send message."

st.title("TaxAssistant by Kraken™")

for chat in st.session_state.messages:
    if chat["user"] == "You":
        st.markdown(f"**You**: {chat['message']}")
    else:
        st.markdown(f"**Assistant**: {chat['message']}")

st.markdown("---")
user_message = st.text_input("Type your message here")

if st.button("Send"):
    if user_message:
        st.session_state.messages.append({"user": "You", "message": user_message})

        bot_reply = send_message(user_message, user_id, conversation_id)
        st.session_state.messages.append({"user": "Bot", "message": bot_reply})

        st.rerun()

st.sidebar.markdown("---")
st.sidebar.write("TaxAssistant help you with your tax related questions.")
