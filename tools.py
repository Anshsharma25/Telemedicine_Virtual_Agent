from langchain.tools import tool
from dotenv import load_dotenv
import os
import requests
import pyttsx3
import speech_recognition as sr

# Load environment variables
load_dotenv()
GOOGLE_MAPS_API_KEY = os.getenv("GOOGLE_MAPS_API_KEY")

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

get_coordinates_tool = get_coordinates

# Tool 2: Find hospitals near coordinates
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

find_hospitals_tool = find_hospitals
