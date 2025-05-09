# tools.py

import os
import json
import requests
from uuid import uuid4
from dotenv import load_dotenv
from langchain.tools import tool
import pyttsx3

# Load environment variables
load_dotenv()

# Text-to-Speech toggle
enable_tts = True
if enable_tts:
    tts_engine = pyttsx3.init()
    def speak_text(text: str):
        print("🗣️ Speaking:", text)
        tts_engine.say(text)
        tts_engine.runAndWait()
else:
    def speak_text(text: str):
        print("🗣️ (TTS Disabled):", text)

# 1) AI Doctor API tool
@tool
def ai_doctor_api_tool(message: str) -> str:
    """
    Call the AI Doctor API to get a medical consultation response for the provided message.
    """
    url = "https://ai-doctor-api-ai-medical-chatbot-healthcare-ai-assistant.p.rapidapi.com/chat?noqueue=1"
    headers = {
        "Content-Type": "application/json",
        "x-rapidapi-host": "ai-doctor-api-ai-medical-chatbot-healthcare-ai-assistant.p.rapidapi.com",
        "x-rapidapi-key": os.getenv("RAPIDAPI_KEY"),
    }
    payload = {"message": message, "specialization": "general", "language": "en"}
    try:
        r = requests.post(url, headers=headers, json=payload)
        if r.status_code != 200:
            return f"API Error: {r.status_code}"
        return r.json().get("message", "No response from API.")
    except Exception as e:
        return f"Error calling AI Doctor API: {e}"

# 2) Check doctor availability tool
@tool
def check_doctor_availability_tool(dummy: str) -> str:
    """
    Reads doctor.json and returns the name of an available doctor, or an error message.
    """
    path = "doctor.json"
    if not os.path.exists(path):
        return "Doctor availability data not found."
    try:
        with open(path) as f:
            for doc in json.load(f):
                if doc.get("status") == "available":
                    return doc["name"]
        return "No doctor is available."
    except Exception as e:
        return f"Error: {e}"

# 3) Generate Jitsi meet link tool
@tool
def generate_meet_link_tool(dummy: str) -> str:
    """
    Generates a unique Jitsi Meet link for telemedicine consultations.
    """
    return f"https://meet.jit.si/telemed-{uuid4()}"
