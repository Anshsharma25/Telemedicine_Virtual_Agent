import os
import re
from dotenv import load_dotenv

from agents import symptom_chain, connect_agent, search_agent
from speech_utils import capture_audio_input, speak_text

load_dotenv()

def main():
    print("\n🤖 Welcome to the AI Health Assistant")
    print("=======================================")
    print("You can describe your symptoms via text, voice, or image.")

    mode = input("\n📝 Input type (text/audio/image): ").strip().lower()

    if mode == "audio":
        user_input = capture_audio_input() or ""

    elif mode == "text":
        user_input = input("🧠 Describe your symptoms: ").strip()

    elif mode == "image":
        image_path = input("📷 Enter image path: ").strip()
        if not image_path:
            print("❌ No image path provided.")
            speak_text("I need an image path to proceed.")
            return

        print("\n🔍 Analyzing image...")
        try:
            from tools import analyze_medical_image
            image_result = analyze_medical_image(image_path)
            print(f"\n📋 Image Analysis Result:\n{image_result}")
            speak_text(image_result)

            # Extract the detected condition from the result
            match = re.search(r"Detected:\s*(.*?)\s*\(", image_result)
            if match:
                user_input = match.group(1)
                print(f"\n📌 Interpreted symptom from image: {user_input}")
            else:
                print("❌ Could not interpret condition from image.")
                speak_text("I could not understand the image result.")
                return

        except Exception as e:
            print(f"❌ Image analysis failed: {e}")
            speak_text("There was a problem analyzing your image.")
            return

    else:
        print("❌ Please choose 'text', 'audio' or 'image'.")
        return

    if not user_input:
        print("❌ Could not capture any input.")
        speak_text("I couldn't hear anything. Please try again.")
        return

    print("\n🔎 Looking up your symptoms for context...")
    try:
        search_results = search_agent.run(user_input)
    except Exception as e:
        print(f"❌ Search failed: {e}")
        search_results = "No additional context available."

    print("\n🤖 Generating your diagnosis...")
    try:
        diagnosis = symptom_chain.run({
            "input": user_input,
            "search_results": search_results
        })
    except Exception as e:
        print(f"\n❌ Error generating diagnosis: {e}")
        speak_text("There was an issue processing your symptoms. Please try again later.")
        return

    print(f"\n💬 Diagnosis:\n{diagnosis}")
    speak_text(diagnosis)

    lower_diag = diagnosis.lower()
    if "immediate medical attention" in lower_diag or "life-threatening" in lower_diag:
        print("\n⚠️ Serious condition detected! Generating your meet link...")
        try:
            connection_output = connect_agent.run("Check availability and generate meet link")
            urls = re.findall(r'https?://\S+', connection_output)
            meet_link = urls[0] if urls else None
        except Exception as e:
            print(f"\n❌ Error generating meet link: {e}")
            meet_link = None

        if not meet_link:
            print("❌ Failed to generate meet link.")
            speak_text("I couldn't generate the meet link. Please consult a professional.")
        else:
            print(f"\n🔗 Consultation link:\n{meet_link}")
            speak_text(f"Your consultation link is {meet_link}.")
    else:
        print("\n👍 Symptoms look non-critical. Please rest and monitor.")
        speak_text("Your symptoms appear mild. Rest and monitor.")

if __name__ == "__main__":
    main()
