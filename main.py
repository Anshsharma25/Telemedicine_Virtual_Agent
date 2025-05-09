# main.py

import os
import re
from dotenv import load_dotenv
from agents import symptom_agent, connect_agent
from speech_utils import capture_audio_input, speak_text

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

    if not user_input:
        print("❌ Could not capture any input.")
        speak_text("I couldn't hear anything. Please try again.")
        return

    print("\n🤖 Checking your symptoms...")
    try:
        response = symptom_agent.invoke(
            {"input": user_input, "chat_history": []},
            handle_parsing_errors=True
        )
        diagnosis = response.get("output", "") if isinstance(response, dict) else str(response)

        if not diagnosis:
            print("\n❌ No diagnosis available. Please try again later.")
            speak_text("Sorry, I couldn't retrieve a diagnosis.")
            return

        print(f"\n💬 Diagnosis:\n{diagnosis}")
        speak_text(diagnosis)
    except Exception as e:
        print(f"\n❌ Error processing symptoms: {e}")
        speak_text("There was an issue processing your symptoms. Please try again later.")
        return

    if "immediate medical attention" in diagnosis.lower() or "life-threatening" in diagnosis.lower():
        print("\n⚠️ Serious condition detected! Generating your meet link...")
        try:
            connection = connect_agent.invoke(
                {"input": "Check availability and generate meet link", "chat_history": []}
            )
            output = connection.get("output", "") if isinstance(connection, dict) else str(connection)
            urls = re.findall(r'https?://\S+', output)
            meet_link = urls[0] if urls else "No link found"

            if meet_link == "No link found":
                print("\n❌ Failed to generate meet link.")
                speak_text("I couldn't generate the meet link. Please consult a professional.")
                return

            print(f"\n🔗 Consultation link:\n{meet_link}")
            speak_text(f"Your consultation link is {meet_link}.")
        except Exception as e:
            print(f"\n❌ Error generating meet link: {e}")
            speak_text("There was an issue generating your consultation link.")
            return
    else:
        print("\n👍 Symptoms look non-critical. Please rest and monitor.")
        speak_text("Your symptoms appear mild. Rest and monitor.")

if __name__ == "__main__":
    main()
