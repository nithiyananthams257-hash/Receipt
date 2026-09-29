import json
import time
from google import genai
from google.genai import types
import streamlit as st
from twilio.rest import Client 

from prompts import SYSTEM_PROMPT, WELCOME_MESSAGE_TEMPLATE, SUMMARY_REQUEST_PROMPT


GENAI_API_KEY = st.secrets.get("GENAI_API_KEY") or st.secrets.get("GEMINI_API_KEY")
TWILIO_ACCOUNT_SID = st.secrets.get("TWILIO_ACCOUNT_SID")
TWILIO_AUTH_TOKEN = st.secrets.get("TWILIO_AUTH_TOKEN")
TWILIO_WHATSAPP_FROM = st.secrets.get("TWILIO_WHATSAPP_FROM")
TWILIO_CONTENT_SID = st.secrets.get("TWILIO_CONTENT_SID")

@st.cache_resource
def configure_genai():
    return genai.Client(api_key=GENAI_API_KEY)

@st.cache_resource
def configure_twilio():
    return Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN) 

twilio_client = configure_twilio()
gemini_client = configure_genai()
MODEL_NAME = "gemini-3.5-flash-lite"

def clean_whatsapp_text(text):
    if not text:
        return "No expense summary available."
    text = " ".join(text.split())  # collapse whitespace/newlines
    return text[:1500] + "..." if len(text) > 1500 else text

def send_whatsapp(to_number, name, summary):
    try:
        from_clean = str(TWILIO_WHATSAPP_FROM).strip().replace("whatsapp:", "").strip()
        if not from_clean.startswith("+"):
            from_clean = "+" + from_clean
        from_number = f"whatsapp:{from_clean}"

        to_clean = str(to_number).strip().replace("whatsapp:", "").strip()
        if not to_clean.startswith("+"):
            to_clean = "+" + to_clean
        dest_number = f"whatsapp:{to_clean}"

        user_name = str(name).strip() if name else "there"
        clean_summary = clean_whatsapp_text(summary)

        content_variables = json.dumps(
            {"1": user_name, "2": clean_summary}, ensure_ascii=False
        )
        message = twilio_client.messages.create(
            from_=from_number,
            to=dest_number,
            content_sid=TWILIO_CONTENT_SID,
            content_variables=content_variables,
        )
        return True, message.sid
    except Exception as e:
        error = str(e)
        print(">>> WhatsApp error:", error)
        return False, error 

def render_message(message):
    with st.chat_message(message["role"]):
        if message["type"] == "text":
            st.write(message["content"])
        elif message["type"] == "image":
            st.image(message["content"])

def add_message(role, msg_type, content):
    st.session_state.messages.append({"role": role, "type": msg_type, "content": content})
    render_message(st.session_state.messages[-1])

def ask_gemini(parts):
    try:
        response = st.session_state.chat.send_message(parts)
        return response.text
    except Exception as e:
        if "503" in str(e) or "UNAVAILABLE" in str(e):
            return "⚠️ The model is currently experiencing high demand. Please retry sending your message in a moment."
        return f"⚠️ Error communicating with Gemini: {e}"

# step 1: onboarding (user name, phone number)
if not st.session_state.get("onboarded"):
    st.title("🧾 Receipt & Expense Tracker")
    st.caption("Snap it. Log it. Text yourself the summary.")

    with st.form("onboarding_form"):
        name = st.text_input("Your name")
        whatsapp_number = st.text_input(
            "WhatsApp number (with country code)",
            placeholder="+91XXXXXXXXXX",
            help="This is the number MacroSnap will text your summary to.",
        )
        submitted = st.form_submit_button("Let's go 🚀")

        if submitted:
            if not name.strip() or not whatsapp_number.strip():
                st.error("Please enter both your name and WhatsApp number.")
            else:
                st.session_state.name = name.strip()
                st.session_state.whatsapp_number = whatsapp_number.strip()
                # activate AI chat
                st.session_state.chat = gemini_client.chats.create(
                    model=MODEL_NAME,
                    config=types.GenerateContentConfig(system_instruction=SYSTEM_PROMPT),
                )
                st.session_state.messages = []
                st.session_state.onboarded = True
                st.rerun()

    st.stop()  # Stop execution until onboarding is complete

# step 2: main chat interface
if "chat" not in st.session_state or getattr(st.session_state.chat, "_model", None) != MODEL_NAME:
    st.session_state.chat = gemini_client.chats.create(
        model=MODEL_NAME,
        config=types.GenerateContentConfig(system_instruction=SYSTEM_PROMPT),
    )

header_col, button_col = st.columns([5, 2], vertical_alignment="center")

with header_col:
    st.title("🧾 Expense Tracker")

with button_col:
    if st.button("📤 Send to WhatsApp", use_container_width=True):
        if not st.session_state.get("whatsapp_number"):
            st.error("WhatsApp number is missing in session.")
        else:
            with st.spinner("Summarizing your expenses..."):
                summary = ask_gemini([SUMMARY_REQUEST_PROMPT])
            with st.spinner("Sending to WhatsApp..."):
                success, info = send_whatsapp(st.session_state.whatsapp_number, st.session_state.name, summary)
            if success:
                st.success("Sent! Check your WhatsApp 📲")
                st.toast("WhatsApp summary sent! 🎉")
            else:
                st.error(f"Couldn't send that: {info}")

st.caption(f"Logged in as {st.session_state.name} - updates go to {st.session_state.whatsapp_number}")

if not st.session_state.messages:
    add_message("assistant", "text", WELCOME_MESSAGE_TEMPLATE.format(name=st.session_state.name))
else:
    for message in st.session_state.messages:
        render_message(message)

user_input = st.chat_input(
    "Describe an expense, or attach a photo of your receipt",
    accept_file=True,
    file_type=["jpg", "jpeg", "png"],
)

if user_input:
    photo = user_input.files[0] if user_input.files else None
    text = user_input.text
    parts = []

    if photo is not None:
        photo_bytes = photo.getvalue()
        add_message("user", "image", photo_bytes)
        parts.append(types.Part.from_bytes(data=photo_bytes, mime_type=photo.type))
    if text:
        add_message("user", "text", text)
        parts.append(text)
    elif photo is not None:
        parts.append("Read this receipt. Give me the merchant, date, items, total and category.")

    with st.spinner("Reading your receipt..."):
        answer = ask_gemini(parts)
    add_message("assistant", "text", answer)

