from agents import symptom_agent, connect_agent
from speech_utils import capture_audio_input, speak_text
from severity_checker import check_symptom_severity
import os
from dotenv import load_dotenv

load_dotenv()

def main():
    print("\n🤖 Welcome to the Agentic AI Health Assistant")
    print("==============================================")
    print("You can describe your symptoms via text or voice.")

    # Step 1: User Input
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

    # Step 2: Symptom Agent invoked
    print("\n🤖 Invoking Symptom Intake Agent...")
    symptom_response = symptom_agent.invoke({
        "input": user_input,
        "chat_history": []  # Placeholder for future memory support
    })

    diagnosis = symptom_response.get("output", "⚠️ No response from symptom agent.")
    print("\n💬 Diagnosis or Guidance:")
    print(diagnosis)
    speak_text(diagnosis)

    # Step 3: Determine Severity
    severity = check_symptom_severity(diagnosis)
    print(f"\n📊 Detected Symptom Severity: {severity.upper()}")

    if severity == "mild":
        print("\n👍 Your symptoms appear to be mild. Follow general advice above.")
    elif severity == "severe":
        # Step 4: Ask if user wants to connect
        connect = input("\n🩺 Your symptoms may be severe. Connect with a doctor? (yes/no): ").strip().lower()
        if connect in ["yes", "y"]:
            print("\n🔄 Connecting with a real-time doctor...")

            connect_response = connect_agent.invoke({
                "input": "Connect me with a real-time doctor.",
                "chat_history": []
            })

            meet_link = connect_response.get("output", "⚠️ Could not connect to a doctor.")
            print("\n📞 Doctor Connection Info:")
            print(meet_link)
            speak_text(meet_link)
        else:
            print("👌 Alright. Stay safe and monitor your symptoms closely.")
    else:
        print("❓ Unable to determine severity. Use your best judgment or consult a professional.")

if __name__ == "__main__":
    main()
