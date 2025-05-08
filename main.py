from agents import symptom_agent, hospital_agent, connect_agent
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

    # Ask if the user wants to connect with a doctor
    connect = input("\n🩺 Do you want to connect with a real-time doctor? (yes/no): ").strip().lower()
    
    if connect in ["yes", "y"]:
        print("\n🔄 Connecting with Doctor via Connect Agent...")

        # Invoke Connect Agent (Agent 3) for doctor connection
        connect_response = connect_agent.invoke({
            "input": "Connect me with a real-time doctor.",
            "chat_history": []  # Add chat history as needed
        })
        
        # Handle the response from Connect Agent
        meet_link = connect_response.get("output", "⚠️ Could not connect to a doctor.")
        print("\n📞 Doctor Connection Info:")
        print(meet_link)
        speak_text(meet_link)
    else:
        print("👍 Okay! Let me know if you need anything else later.")

if __name__ == "__main__":
    main()
