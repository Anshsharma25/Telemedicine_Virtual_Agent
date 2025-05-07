from agents import symptom_agent, hospital_agent
from speech_utils import capture_audio_input, speak_text
import os
from dotenv import load_dotenv

load_dotenv()

def main():
    print("\n🤖 Welcome to the AI Health Assistant")
    print("=======================================")
    print("You can describe your symptoms via text or voice.")
    
    input_mode = input("\n📝 Enter input type (text/audio): ").strip().lower()

    if input_mode == "audio":
        user_input = capture_audio_input()
        if not user_input:
            print("❌ No valid audio detected. Exiting...")
            return
    elif input_mode == "text":
        user_input = input("🧠 Describe your symptoms: ").strip()
    else:
        print("❌ Invalid input type. Please choose 'text' or 'audio'.")
        return

    # Agent 1: Symptom Intake
    print("\n🤖 Invoking Symptom Intake Agent...")
    symptom_response = symptom_agent.invoke({
        "input": user_input,
        "chat_history": []  # Add empty chat history to satisfy agent input
    })

    diagnosis = symptom_response.get("output", "⚠️ No response from symptom agent.")
    print("\n💬 Diagnosis or Guidance:")
    print(diagnosis)
    speak_text(diagnosis)

    # Ask about hospital locator
    follow_up = input("\n🗺️ Do you want to find top hospitals near you? (yes/no): ").strip().lower()
    if follow_up in ["yes", "y"]:
        address = input("📍 Enter your full address (with city): ").strip()
        if not address:
            print("⚠️ Address is required to find hospitals.")
            return

        print("\n🤖 Invoking Hospital Finder Agent...")
        hospital_response = hospital_agent.invoke({
            "input": f"Find top hospitals near {address}",
            "chat_history": []
        })

        hospital_list = hospital_response.get("output", "⚠️ No hospital data returned.")
        print("\n🏥 Nearby Hospitals:")
        print(hospital_list)
        speak_text(hospital_list)
    else:
        print("👍 Alright. Feel free to ask anything else later!")

if __name__ == "__main__":
    main()
