<<<<<<< HEAD
'''
+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
PHASE 1: Taking input from the user and passing it to the model in the form of Text or Audio.
+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
'''
import os
import requests
import speech_recognition as sr
import pyttsx3
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI

# Load environment variables
load_dotenv()
GOOGLE_MAPS_API_KEY = os.getenv("GOOGLE_MAPS_API_KEY")

# Initialize the Gemini model and text-to-speech engine
model = ChatGoogleGenerativeAI(model='gemini-1.5-flash-latest')
tts_engine = pyttsx3.init()

# Speak the given text aloud
def speak_text(text):
    print("🗣️ Speaking the simplified explanation...")
    tts_engine.say(text)
    tts_engine.runAndWait()

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
        f"&radius=50000"
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

    # Step 1: Get model's main response
    result = model.invoke(user_input)
    original_response = result.content
    print("\n🤖 Agent response:", original_response)

    # Step 2: Ask model to explain the response in simple terms
    explanation_prompt = f"Explain this response in very simple terms suitable for a 5-year-old:\n\n{original_response}"
    simple_explanation = model.invoke(explanation_prompt).content
    print("\n🗣️ Simplified Explanation:")
    print(simple_explanation)

    # Step 3: Speak the simplified explanation
    speak_text(simple_explanation)

    # # Follow-up question
    # follow_up = input("\n🤖 Do you want to find the top 5 hospitals near your area? (yes/no): ").strip().lower()
    # if follow_up in ["yes", "y"]:
    #     address = input("\nPlease provide your address: ").strip()
    #     lat, lng = get_coordinates_from_address(address)
    #     if lat is None or lng is None:

    
    #         print("⚠️ Unable to find hospitals without a valid location.")
    #         return
    #     hospital_list = find_nearby_hospitals(lat, lng)
    #     print(hospital_list)
    #     speak_text(hospital_list)
    # else:
    #     print("👍 Okay! Let me know if you need anything else.")
=======
import os
from dotenv import load_dotenv
from agents import symptom_agent, connect_agent  # Import the agents
from speech_utils import capture_audio_input, speak_text

# Load environment variables from .env
load_dotenv()

def main():
    # Introduction
    print("\n🤖 Welcome to the AI Health Assistant")
    print("=======================================")
    print("You can describe your symptoms via text or voice.")
    
    # Prompt user for input method (audio or text)
    mode = input("\n📝 Input type (text/audio): ").strip().lower()

    # Handle user input based on the selected mode
    if mode == "audio":
        user_input = capture_audio_input() or ""
    elif mode == "text":
        user_input = input("🧠 Describe your symptoms: ").strip()
    else:
        print("❌ Please choose 'text' or 'audio'.")
        return

    # Step 1: Symptom Intake & Diagnosis
    print("\n🤖 Checking your symptoms...")
    try:
        response = symptom_agent.invoke({
            "input": user_input,
            "chat_history": []  # Empty chat history for fresh interactions
        }, handle_parsing_errors=True)  # Enable parsing error handling
        
        diagnosis = response.get("output", "")
        
        if not diagnosis:
            print("\n❌ No diagnosis available. Please try again later.")
            speak_text("Sorry, I couldn't retrieve a diagnosis at the moment.")
            return
        
        print(f"\n💬 Diagnosis:\n{diagnosis}")
        speak_text(diagnosis)  # Speak the diagnosis aloud
    except Exception as e:
        print(f"\n❌ An error occurred while processing symptoms: {e}")
        speak_text("Sorry, there was an issue processing your symptoms. Please try again later.")
        return

    # Step 2: Serious case check → Generate meet link if required
    if "immediate medical attention" in diagnosis.lower() or "life-threatening" in diagnosis.lower():
        print("\n⚠️ Serious condition detected! Generating your meet link...")
        try:
            connection = connect_agent.invoke({
                "input": "Check availability and generate meet link",  # Query the connect agent
                "chat_history": []  # Empty chat history for fresh query
            })
            output = connection.get("output", "")
            
            if not output:
                print("\n❌ Failed to generate meet link. Please consult a healthcare professional directly.")
                speak_text("I couldn't generate the meet link. Please consult a healthcare professional.")
                return

            meet_link = output.strip().split()[-1]  # Extract last token as link
            print(f"\n🔗 Your Jitsi Meet link (please share this with your doctor):\n{meet_link}")
            print("🕒 Your doctor will join you there in a few minutes.")
            speak_text(f"Your consultation link is {meet_link}. Your doctor will connect in a few minutes.")
        except Exception as e:
            print(f"\n❌ An error occurred while generating the meet link: {e}")
            speak_text("Sorry, I couldn't generate a meet link. Please try again later.")
            return
    else:
        # Step 3: Non-critical case
        print("\n👍 Symptoms look non-critical. Please rest and monitor, and reach out if things worsen.")
        speak_text("Your symptoms appear mild. Rest and monitor.")
>>>>>>> origin/Agentic_Ai

if __name__ == "__main__":
    main()
