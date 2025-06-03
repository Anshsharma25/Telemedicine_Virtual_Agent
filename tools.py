import os
import json
import requests
from uuid import uuid4
from dotenv import load_dotenv
from langchain_community.tools import tool
from serpapi import GoogleSearch
import pyttsx3
from roboflow import Roboflow
from langchain_core.tools import tool  # Use this import instead


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



import os
from roboflow import Roboflow

def analyze_medical_image(image_path: str, category: str) -> str:
    """Analyze a medical image using multiple Roboflow models based on category."""

    if not os.path.exists(image_path):
        return f"❌ Image not found: {image_path}"

    rf = Roboflow(api_key="UWOU2vqDDSIsfBphWxJU")  # Replace with your actual key

    # Define model info per category (manual category input)
    category_models = {
        "skin": {
            "model_id": "health-bqeyj",
            "version": 1,
            "valid_classes": ["Ringworm", "Basal Cell Carcinoma", "Eczema", "Psoriasis", "Acne"]
        },
        "dental": {
            "model_id": "dental-gjlh1",
            "version": 1,
            "valid_classes": ["Tooth Decay", "Cavity", "Plaque", "Healthy Tooth"]
        },
        "eye": {
            "model_id": "classification_data",
            "version": 1,
            "valid_classes": ["Cataract", "Glaucoma", "Normal", "Red Eye"]
        },
        "hair": {
            "model_id": "hair-disease-detection-o2ok0-vqwpb",
            "version": 1,
            "valid_classes": ["Alopecia", "Dandruff", "Psoriasis", "Folliculitis", "Healthy Scalp"]
        }
    }

    if category not in category_models:
        return f"❌ Invalid category '{category}'. Please choose from {list(category_models.keys())}"

    model_info = category_models[category]

    try:
        project = rf.workspace().project(model_info["model_id"])
        model = project.version(model_info["version"]).model
        prediction = model.predict(image_path).json()
    except Exception as e:
        return f"❌ Failed to analyze image with {category} model: {e}"

    results = []
    max_confidence = 0
    final_prediction = None

    for pred in prediction.get("predictions", []):
        class_name = pred.get("class")
        confidence = round(pred.get("confidence", 0) * 100, 2)

        # Ignore classes not in valid classes list
        if class_name not in model_info["valid_classes"]:
            continue

        results.append(f"🩺 Detected: {class_name} ({confidence}% confidence)")

        if confidence > max_confidence:
            max_confidence = confidence
            final_prediction = (class_name, confidence)

    if not results:
        return "✅ No valid medical conditions detected in the image."

    summary = "\n".join(results)
    if final_prediction:
        name, conf = final_prediction
        summary += f"\n\n🔬 Based on the highest confidence, primary concern is: **{name}** ({conf}% confidence)"

    return summary
