from langchain.tools import tool
from dotenv import load_dotenv
import os
import requests
import pyttsx3
import json
from uuid import uuid4

# Load environment variables
load_dotenv()
GOOGLE_MAPS_API_KEY = os.getenv("GOOGLE_MAPS_API_KEY")

# TTS engine setup (not a tool)
tts_engine = pyttsx3.init()
def speak_text(text: str):
    print("🗣️ Speaking:", text)
    tts_engine.say(text)
    tts_engine.runAndWait()

# Tool 1: Symptom Checker using AI Doctor API
@tool
def ai_doctor_api_tool(message: str) -> str:
    """Use AI Doctor API to analyze symptoms and return diagnosis."""
    url = "https://ai-doctor-api-ai-medical-chatbot-healthcare-ai-assistant.p.rapidapi.com/chat?noqueue=1"
    headers = {
        "Content-Type": "application/json",
        "x-rapidapi-host": "ai-doctor-api-ai-medical-chatbot-healthcare-ai-assistant.p.rapidapi.com",
        "x-rapidapi-key": os.getenv("RAPIDAPI_KEY")
    }
    payload = {"message": message, "specialization": "general", "language": "en"}
    try:
        r = requests.post(url, headers=headers, json=payload)
        if r.status_code != 200:
            return f"API Error: {r.status_code}"
        return r.json().get("message", "No response from API.")
    except Exception as e:
        return f"Error calling AI Doctor API: {e}"

# Tool 2: Check availability of doctor
@tool
def check_doctor_availability(dummy: str) -> str:
    """Check if any doctor is available. Input is ignored."""
    try:
        with open("doctor.json") as f:
            for doc in json.load(f):
                if doc.get("status") == "available":
                    return doc["name"]
        return "No doctor is available."
    except Exception as e:
        return f"Error: {e}"

# Tool 3: Generate a meeting link
@tool
def generate_meet_link_tool(dummy: str) -> str:
    """Generate a secure Jitsi Meet link. Input is ignored."""
    return f"https://meet.jit.si/telemed-{uuid4()}"

# If needed later, uncomment and wrap these similarly:
# @tool
# def get_coordinates_tool(address: str) -> str:
#     """Get latitude and longitude from an address using Google Maps API."""
#     ...

# @tool
# def find_hospitals_tool(location: str) -> str:
#     """Find top hospitals near a given lat,long location using Google Maps API."""
#     ...

# Expose tools
# get_coordinates_tool = get_coordinates
# find_hospitals_tool = find_hospitals
check_doctor_availability_tool = check_doctor_availability
generate_meet_link_tool = generate_meet_link_tool
