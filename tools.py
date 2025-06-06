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
        snippet = item.get("snippet","").strip()
        link = item.get("link","").strip()
        results.append(f"🔹 {title}\n{snippet}\n🔗 {link}")
    return "\n\n".join(results)


def analyze_medical_image(image_path: str) -> str:
    """Analyze medical image with multiple Roboflow models and aggregate results with descriptive report."""

    if not os.path.exists(image_path):
        return f"❌ Image not found: {image_path}"

    rf = Roboflow(api_key="UWOU2vqDDSIsfBphWxJU")  # Your Roboflow API key

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

    # Disease info dict for skin category (you can add more for dental, eye, hair if needed)
    disease_info_skin = {
        "Ringworm": {
            "description": "ek fungal infection hai jo skin par circular patches banata hai",
            "symptoms": "redness, itching, circular rash",
            "treatment": "antifungal creams aur proper hygiene zaruri hai"
        },
        "Basal Cell Carcinoma": {
            "description": "skin cancer ka ek common type hai jo slowly grow karta hai",
            "symptoms": "skin par lumps ya sores jo heal nahi hote",
            "treatment": "doctor se consult karna aur surgery ya radiation therapy ho sakti hai"
        },
        "Eczema": {
            "description": "ek skin allergy hai jisme skin dry aur irritated ho jati hai",
            "symptoms": "dryness, redness, itching",
            "treatment": "moisturizers aur steroid creams ka use karna chahiye"
        },
        "Psoriasis": {
            "description": "ek autoimmune skin condition hai jisme red patches aur scaling hoti hai",
            "symptoms": "red patches, scaling, itching",
            "treatment": "medicated creams, light therapy, aur doctor ki salah zaruri hai"
        },
        "Acne": {
            "description": "skin ki sebaceous glands ki problem hai, jo pimples banati hai",
            "symptoms": "pimples, blackheads, oily skin",
            "treatment": "face wash, antibiotics, aur doctor se consult karna chahiye"
        }
    }

    all_results = []
    best_prediction = None
    max_confidence = 0

    for cat, model_info in category_models.items():
        try:
            project = rf.workspace().project(model_info["model_id"])
            model = project.version(model_info["version"]).model
            prediction = model.predict(image_path).json()
        except Exception as e:
            all_results.append(f"❌ Failed to analyze with {cat} model: {e}")
            continue

        for pred in prediction.get("predictions", []):
            class_name = pred.get("class")
            confidence = round(pred.get("confidence", 0) * 100, 2)

            if class_name not in model_info["valid_classes"]:
                continue

            all_results.append(f"🩺 [{cat}] Detected: {class_name} ({confidence}% confidence)")

            if confidence > max_confidence:
                max_confidence = confidence
                best_prediction = (cat, class_name, confidence)

    if not all_results:
        return "✅ No valid medical conditions detected by any model."

    summary = "\n".join(all_results)

    if best_prediction:
        cat, name, conf = best_prediction

        # Generate descriptive report for skin category only here; expand as needed
        if cat == "skin" and name in disease_info_skin:
            info = disease_info_skin[name]
            report = (
                f"\n\n🔬 Highest confidence from '{cat}' model: **{name}** ({conf}%)\n"
                f"Is image mein {name} ({info['description']}) ke lakshan dikh rahe hain, "
                f"jaise {info['symptoms']}. Treatment mein {info['treatment']}. "
                f"Doctor se salah lena zaruri hai."
            )
            summary += report
        else:
            summary += f"\n\n🔬 Highest confidence from '{cat}' model: **{name}** ({conf}%)"

    return summary
