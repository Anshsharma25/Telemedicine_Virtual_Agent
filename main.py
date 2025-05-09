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

if __name__ == "__main__":
    main()
