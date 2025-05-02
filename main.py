'''
+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
PHASE 1: Taking input from the user and passing it to the model in the form of Text or Audio.
+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
'''
import os
import requests
import speech_recognition as sr
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI

# Load environment variables
load_dotenv()
GOOGLE_MAPS_API_KEY = os.getenv("GOOGLE_MAPS_API_KEY")

# Initialize the Gemini model
model = ChatGoogleGenerativeAI(model='gemini-1.5-pro')

# Capture audio input and convert to text
def capture_audio_input():
    recognizer = sr.Recognizer()
    microphone = sr.Microphone()
    print("🎙️ Listening... Please speak.")

    with microphone as source:
        recognizer.adjust_for_ambient_noise(source)
        audio = recognizer.listen(source)

    try:
        text = recognizer.recognize_google(audio)
        print(f"📝 Recognized Text: {text}")
        return text
    except sr.UnknownValueError:
        print("❌ Could not understand the audio.")
        return None
    except sr.RequestError:
        print("❌ Could not request results. Check your internet.")
        return None

# Convert address to latitude and longitude using Google Geocoding API
def get_coordinates_from_address(address):
    geocoding_url = f"https://maps.googleapis.com/maps/api/geocode/json?address={address}&key={GOOGLE_MAPS_API_KEY}"
    response = requests.get(geocoding_url)
    data = response.json()

    if data["status"] == "OK":
        lat = data["results"][0]["geometry"]["location"]["lat"]
        lng = data["results"][0]["geometry"]["location"]["lng"]
        print(f"📍 Location from Address: Latitude = {lat}, Longitude = {lng}")
        return lat, lng
    else:
        print("❌ Failed to get coordinates from the address.")
        return None, None

# Get top 5 hospitals using Google Maps API
def find_nearby_hospitals(lat, lng):
    url = (
        f"https://maps.googleapis.com/maps/api/place/nearbysearch/json"
        f"?location={lat},{lng}"
        f"&radius=50000"  # 50 km max allowed
        f"&type=hospital"
        f"&key={GOOGLE_MAPS_API_KEY}"
    )
    response = requests.get(url)
    data = response.json()
    results = data.get("results", [])

    if not results:
        return "🚫 No hospitals found nearby."

    response_lines = ["\n🏥 Top 5 Hospitals within 50 km:\n"]
    for place in results[:5]:
        name = place.get("name")
        rating = place.get("rating", "N/A")
        address = place.get("vicinity", "Address not available")
        response_lines.append(f"- {name} | ⭐ {rating} | 📍 {address}")
    
    return "\n".join(response_lines)

# Main logic
def main():
    input_type = input("Enter input type (text/audio): ").strip().lower()

    if input_type == "text":
        user_input = input("Enter the Issue: ")
    elif input_type == "audio":
        user_input = capture_audio_input()
        if not user_input:
            print("❌ No valid audio input detected.")
            return
    else:
        print("❌ Invalid input type. Please enter 'text' or 'audio'.")
        return

    result = model.invoke(user_input)
    print("\n🤖 Agent response:", result.content)

    # Follow-up question
    follow_up = input("\n🤖 Do you want to find the top 5 hospitals near your area? (yes/no): ").strip().lower()
    if follow_up in ["yes", "y"]:
        # Ask for user input for address
        address = input("\nPlease provide your address: ").strip()
        lat, lng = get_coordinates_from_address(address)
        if lat is None or lng is None:
            print("⚠️ Unable to find hospitals without a valid location.")
            return
        hospital_list = find_nearby_hospitals(lat, lng)
        print(hospital_list)
    else:
        print("👍 Okay! Let me know if you need anything else.")

if __name__ == "__main__":
    main()
