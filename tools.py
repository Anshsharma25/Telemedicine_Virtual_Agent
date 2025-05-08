from langchain.tools import tool
from dotenv import load_dotenv
import os
import requests
import pyttsx3
import speech_recognition as sr
import json
from uuid import uuid4
from twilio.rest import Client

# Load environment variables
load_dotenv()
GOOGLE_MAPS_API_KEY = os.getenv("GOOGLE_MAPS_API_KEY")
TWILIO_SID = os.getenv("TWILIO_SID")
TWILIO_AUTH = os.getenv("TWILIO_AUTH")
TWILIO_PHONE = os.getenv("TWILIO_PHONE")
client = Client(TWILIO_SID, TWILIO_AUTH)

# TTS engine setup
tts_engine = pyttsx3.init()

# Speak text (used only inside main, not needed as tool)
def speak_text(text):
    print("🗣️ Speaking the simplified explanation...")
    tts_engine.say(text)
    tts_engine.runAndWait()

# Tool 1: Get coordinates from address
@tool
def get_coordinates(address: str) -> str:
    """Get latitude and longitude of a given address."""
    url = f"https://maps.googleapis.com/maps/api/geocode/json?address={address}&key={GOOGLE_MAPS_API_KEY}"
    res = requests.get(url).json()
    if res["status"] == "OK":
        loc = res["results"][0]["geometry"]["location"]
        return f"{loc['lat']},{loc['lng']}"
    return "Invalid address."

# Tool 2: Symptom Checker using AI Doctor API
@tool
def ai_doctor_api_tool(message: str) -> str:
    """Chat with a medical AI assistant. Input should be a health-related question or symptom description."""
    url = "https://ai-doctor-api-ai-medical-chatbot-healthcare-ai-assistant.p.rapidapi.com/chat?noqueue=1"
    headers = {
        "Content-Type": "application/json",
        "x-rapidapi-host": "ai-doctor-api-ai-medical-chatbot-healthcare-ai-assistant.p.rapidapi.com",
        "x-rapidapi-key": os.getenv("RAPIDAPI_KEY")
    }
    payload = {
        "message": message,
        "specialization": "general",
        "language": "en"
    }

    try:
        response = requests.post(url, headers=headers, json=payload)
        if response.status_code != 200:
            return f"API Error: {response.status_code} - {response.text}"

        return response.json().get("message", "No response from API.")
    except Exception as e:
        return f"Error calling AI Doctor API: {str(e)}"

# Tool 3: Find hospitals near coordinates
@tool
def find_hospitals(location: str) -> str:
    """Find top 5 hospitals near a given 'lat,lng'."""
    url = f"https://maps.googleapis.com/maps/api/place/nearbysearch/json?location={location}&radius=50000&type=hospital&key={GOOGLE_MAPS_API_KEY}"
    res = requests.get(url).json()
    results = res.get("results", [])

    if not results:
        return "No hospitals found nearby."

    lines = ["🏥 Top 5 Hospitals:\n"]
    for place in results[:5]:
        name = place.get("name")
        rating = place.get("rating", "N/A")
        addr = place.get("vicinity", "N/A")
        lines.append(f"- {name} | ⭐ {rating} | 📍 {addr}")
    return "\n".join(lines)

# Tool 4: Check availability of doctor
@tool
def check_doctor_availability() -> str:
    """Check if a doctor is available."""
    try:
        with open("doctors.json", "r") as file:
            doctors = json.load(file)
        for doctor in doctors:
            if doctor['status'] == 'available':
                return doctor['name']
        return "No doctor is available."
    except Exception as e:
        return f"Error: {str(e)}"

# Tool 5: Generate a meeting link
@tool
def generate_meet_link_tool() -> str:
    """Generate a unique Jitsi Meet link."""
    return f"https://meet.jit.si/telemed-{uuid4()}"

# Tool 6: Send meeting link to user via SMS
@tool
def send_meet_sms_tool(phone_and_link: str) -> str:
    """Send a video call link to a user's phone via SMS using Twilio."""
    try:
        phone, link = phone_and_link.split(',')
        client.messages.create(
            body=f"Doctor is ready. Join here: {link.strip()}",
            from_=TWILIO_PHONE,
            to=phone.strip()
        )
        return f"Message sent to {phone.strip()}"
    except Exception as e:
        return f"Error: {str(e)}"

# ✅ Fix: Assign tool references to variables for external import
get_coordinates_tool = get_coordinates
ai_doctor_api_tool = ai_doctor_api_tool
find_hospitals_tool = find_hospitals
check_doctor_availability_tool = check_doctor_availability
generate_meet_link_tool = generate_meet_link_tool
send_meet_sms_tool = send_meet_sms_tool
