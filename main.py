from agents import symptom_agent, connect_agent
from speech_utils import capture_audio_input, speak_text
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def main():
    print("\n🤖 Welcome to the AI Health Assistant")
    print("=======================================")
    print("You can describe your symptoms via text or voice.")
    
    mode = input("\n📝 Input type (text/audio): ").strip().lower()
    if mode == "audio":
        user_input = capture_audio_input() or ""
    elif mode == "text":
        user_input = input("🧠 Describe your symptoms: ").strip()
    else:
        print("❌ Please choose 'text' or 'audio'.")
        return

    # Step 1: Symptom Intake
    print("\n🤖 Checking your symptoms...")
    response = symptom_agent.invoke({
        "input": user_input,
        "chat_history": []
    })
    diagnosis = response.get("output", "")
    print(f"\n💬 Diagnosis:\n{diagnosis}")
    speak_text(diagnosis)

    # Step 2: Serious case check → Generate meet link
    if "immediate medical attention" in diagnosis.lower() or "life-threatening" in diagnosis.lower():
        print("\n⚠️ Serious condition detected! Generating your meet link...")
        connection = connect_agent.invoke({
            "input": "Check availability and generate meet link",
            "chat_history": []
        })
        output = connection.get("output", "")
        meet_link = output.strip().split()[-1]  # Extract last token as link
        print(f"\n🔗 Your Jitsi Meet link (please share this with your doctor):\n{meet_link}")
        print("🕒 Your doctor will join you there in a few minutes.")
        speak_text(f"Your consultation link is {meet_link}. Your doctor will connect in a few minutes.")
    else:
        print("\n👍 Symptoms look non-critical. Please rest and monitor, and reach out if things worsen.")
        speak_text("Your symptoms appear mild. Rest and monitor.")

if __name__ == "__main__":
    main()
