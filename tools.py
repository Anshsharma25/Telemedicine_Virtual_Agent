import os
import json
import requests
from uuid import uuid4
from dotenv import load_dotenv
from langchain_community.tools import tool
from serpapi import GoogleSearch
import pyttsx3

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

# 1) Check doctor availability tool
tool_tip = "Reads doctor.json and returns an available doctor's name."
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

# 2) Jitsi Meet link generator tool
@tool
def generate_meet_link_tool(dummy: str) -> str:
    """
    Generates a unique Jitsi Meet link for telemedicine consultations.
    """
    return f"https://meet.jit.si/telemed-{uuid4()}"

# 3) Medical symptom search via SerpAPI
doc_search = "Uses SerpAPI to fetch symptom info from trusted medical sites."
@tool
def search_medical(query: str) -> str:
    """
    Searches trusted medical sites (Mayo Clinic, WebMD, NHS) for the given symptom using SerpAPI and returns top 3 results.
    """
    API_KEY = os.getenv("SERPAPI_API_KEY")
    if not API_KEY:
        return "Error: SERPAPI_API_KEY not set in environment."

    params = {
        "engine":      "google",
        "q":           f"{query} site:mayoclinic.org OR site:webmd.com OR site:nhs.uk",
        "api_key":     API_KEY,
        "num":         5,
    }
    client = GoogleSearch(params)
    data   = client.get_dict()
    hits   = data.get("organic_results", [])
    if not hits:
        return "No results found."

    results = []
    for item in hits[:3]:
        title = item.get("title","").strip()
        snippet = item.get("snippet",""
                           ).strip()
        link = item.get("link",""
                         ).strip()
        results.append(f"🔹 {title}\n{snippet}\n🔗 {link}")
    return "\n\n".join(results)