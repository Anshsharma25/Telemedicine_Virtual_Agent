import re
from dotenv import load_dotenv
from agents import symptom_chain, connect_agent, search_agent  # Removed followup_chain import
from speech_utils import capture_audio_input, speak_text

load_dotenv()

EXIT_COMMANDS = {"by", "exit", "quit", "bye"}

def check_exit(user_input):
    return user_input.strip().lower() in EXIT_COMMANDS

def print_chat_history(history):
    print("\n🗨 Chat History:")
    for i, (inp, resp) in enumerate(history, 1):
        print(f"{i}. You: {inp}")
        print(f"   Assistant: {resp}\n")

def speak_response(response):
    if hasattr(response, "content"):
        text_to_speak = response.content
    elif isinstance(response, dict) and "content" in response:
        text_to_speak = response["content"]
    else:
        text_to_speak = str(response)
    speak_text(text_to_speak)
    return text_to_speak

def main():
    print("\n🤖 Welcome to the AI Health Assistant")
    print("=======================================")
    print("You can describe your symptoms via text, voice, or image.")
    print("Type 'exit', 'by', or 'quit' anytime to exit.\n")

    chat_history = []

    while True:
        mode = input("📝 Input type (text/audio/image): ").strip().lower()
        if check_exit(mode):
            print("👋 Exiting...")
            print_chat_history(chat_history)
            break

        print("You can describe your symptoms in detail; otherwise, you may not get better results.")

        if mode == "audio":
            user_input = capture_audio_input() or ""
            if check_exit(user_input):
                print("👋 Exiting...")
                print_chat_history(chat_history)
                break

        elif mode == "text":
            user_input = input("🧠 Describe your symptoms: ").strip()
            if check_exit(user_input):
                print("👋 Exiting...")
                print_chat_history(chat_history)
                break

        elif mode == "image":
            image_path = input("📷 Enter image path: ").strip()
            if check_exit(image_path):
                print("👋 Exiting...")
                print_chat_history(chat_history)
                break

            if not image_path:
                print("❌ No image path provided.")
                speak_text("I need an image path to proceed.")
                continue

            print("\n🔍 Analyzing image...")
            try:
                from tools import analyze_medical_image
                image_result = analyze_medical_image(image_path)
                print(f"\n📋 Image Analysis Result:\n{image_result}")
                speak_text(image_result)

                match = re.search(r"Highest confidence from '(\w+)' model: \*\*(.*?)\*\* \(([\d\.]+)%\)", image_result)
                if match:
                    condition = match.group(2)
                    print(f"\n📌 Interpreted symptom from image: {condition}")
                    user_input = condition
                else:
                    detected_match = re.search(r"Detected:\s*(.*?)\s*\(", image_result)
                    if detected_match:
                        user_input = detected_match.group(1)
                        print(f"\n📌 Interpreted symptom from image: {user_input}")
                    else:
                        print("❌ Could not interpret condition from image.")
                        speak_text("I could not understand the image result.")
                        continue

            except Exception as e:
                print(f"❌ Image analysis failed: {e}")
                speak_text("There was a problem analyzing your image.")
                continue

        else:
            print("❌ Please choose 'text', 'audio' or 'image'.")
            continue

        if not user_input:
            print("❌ Could not capture any input.")
            speak_text("I couldn't hear anything. Please try again.")
            continue

        user_location = input("\n📍 Enter your location (e.g., Noida, Mumbai): ").strip()
        if check_exit(user_location):
            print("👋 Exiting...")
            print_chat_history(chat_history)
            break

        print("\n🔎 Looking up your symptoms for context...")
        try:
            search_query = f"{user_input} near {user_location}"
            search_results = search_agent.run(search_query)
        except Exception as e:
            print(f"❌ Search failed: {e}")
            search_results = "No additional context available."

        # ====== UPDATED: No separate follow-up question step ======
        print("\n🤖 Generating your follow-up questions and diagnosis in one response...")
        try:
            diagnosis_response = symptom_chain.run({
                "input": user_input,
                "search_results": search_results,
                "user_location": user_location
            })
            print(f"\n💬 Assistant Response:\n{diagnosis_response}")
            diagnosis = speak_response(diagnosis_response)
        except Exception as e:
            print(f"\n❌ Error generating response: {e}")
            speak_text("There was an issue processing your symptoms. Please try again later.")
            continue

        chat_history.append((user_input, diagnosis))

        lower_diag = diagnosis.lower()
        if "immediate medical attention" in lower_diag or "life-threatening" in lower_diag:
            print("\n⚠ Serious condition detected! Generating your meet link...")
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
