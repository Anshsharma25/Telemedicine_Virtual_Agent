import re
import uuid
from dotenv import load_dotenv
from agents import symptom_chain, connect_agent, search_agent, followup_chain
from speech_utils import capture_audio_input, speak_text
from document import *
from Database.DB import *
from Appointment import show_available_doctors, book_appointment

load_dotenv()

EXIT_COMMANDS = {"by", "exit", "quit", "bye"}

def check_exit(user_input): 
    return user_input.strip().lower() in EXIT_COMMANDS

def print_chat_history(history):
    print("\n\U0001F5E8 Chat History:")
    for i, (inp, resp) in enumerate(history, 1):
        print(f"{i}. You: {inp}")
        print(f"   Assistant: {resp}\n")

def speak_response(response):
    if hasattr(response, "content"):
        return response.content
    elif isinstance(response, dict) and "content" in response:
        return response["content"]
    else:
        return str(response)

def combine_reports(prev_symptoms, prev_diagnosis, new_symptoms, gender):
    return (
        f"\U0001F4DE Patient Medical History:\n"
        f"👤 Gender: {gender}\n"
        f"🕓 Previous Symptoms: {prev_symptoms}\n"
        f"🩺 Previous Diagnosis: {prev_diagnosis}\n"
        f"🆕 New Reported Symptoms: {new_symptoms}\n"
        f"👉 Based on all of the above, give updated diagnosis and suggestions."
    )

def main():
    print("\n\U0001F916 Welcome to the AI Health Assistant")
    print("=======================================")
    print("You can describe your symptoms via text, voice, image, or document.")
    print("Type 'exit', 'by', or 'quit' anytime to exit.\n")

    create_table()
    chat_history = []

    while True:
        visited_before = input("\U0001F9D1‍⚕ Have you visited before? (yes/no): ").strip().lower()
        if check_exit(visited_before):
            print("\U0001F44B Exiting...")
            print_chat_history(chat_history)
            break

        gender = input("⚧️ What is your gender (male/female/other): ").strip()
        if check_exit(gender):
            print("\U0001F44B Exiting...")
            break

        user_record = None
        is_new_user = False
        previous_diagnosis = ""

        if visited_before in ("yes", "y"):
            existing_id = input("\U0001F511 Please enter your previous User ID: ").strip()
            user_record = get_user(existing_id)

            if user_record:
                previous_diagnosis = user_record[4]
                print(f"\n\U0001F4CB Previous Record Found:")
                print(f"  - Name: {user_record[1]}")
                print(f"  - Previous Symptoms: {user_record[2]}")
                print(f"  - Previous Diagnosis: {previous_diagnosis}")

                progress = input("\U0001F501 Have your symptoms improved? (yes/no): ").strip().lower()
                if progress in {"yes", "y"}:
                    print("\U0001F60A Great! You seem to be improving. No further action required.")
                    speak_text("I'm glad to hear you're feeling better. Take care!")
                    break
                name = user_record[1]
                user_id = existing_id
            else:
                print("❌ User ID not found. Let's register you as a new user.")
                is_new_user = True

        if visited_before == "no" or is_new_user:
            name = input("\U0001F4DD Please enter your name: ").strip()
            user_id = str(uuid.uuid4())[:8]
            print(f"\U0001F194 Your new User ID is: {user_id}")

        mode = input("\U0001F4DD Input type (text/audio/image/document): ").strip().lower()
        if check_exit(mode):
            print("\U0001F44B Exiting...")
            break

        print("You can describe your symptoms in detail; otherwise, you may not get better results.")
        user_input = ""

        if mode == "audio":
            user_input = capture_audio_input() or ""

        elif mode == "text":
            user_input = input("\U0001F9E0 Describe your symptoms: ").strip()

        elif mode == "document":
            file_path = input("\U0001F4C4 Enter the patient report PDF path: ").strip()
            if check_exit(file_path):
                print("\U0001F44B Exiting...")
                break
            try:
                user_input = maindocument(file_path)
                if not user_input:
                    print("❌ Failed to extract symptoms from the PDF.")
                    speak_text("Sorry, I could not extract any medical information from the document.")
                    continue
            except Exception as e:
                print(f"❌ Document processing failed: {e}")
                speak_text("There was a problem processing the document.")
                continue

        elif mode == "image":
            image_path = input("\U0001F4F7 Enter image path: ").strip()
            if check_exit(image_path):
                print("\U0001F44B Exiting...")
                break
            try:
                from tools import analyze_medical_image
                image_result = analyze_medical_image(image_path)
                print(f"\n\U0001F4CB Image Analysis Result:\n{image_result}")
                speak_text(image_result)
                match = re.search(r"Detected:\s*(.*?)\\(", image_result)
                user_input = match.group(1) if match else ""
            except Exception as e:
                print(f"❌ Image analysis failed: {e}")
                speak_text("There was a problem analyzing your image.")
                continue

        else:
            print("❌ Please choose 'text', 'audio', 'image', or 'document'.")
            continue

        if not user_input:
            print("❌ Could not capture any input.")
            speak_text("I couldn't hear anything. Please try again.")
            continue

        user_location = input("\n\U0001F4CD Enter your location (e.g., Noida, Mumbai): ").strip()
        if check_exit(user_location):
            print("\U0001F44B Exiting...")
            break

        print("\n\U0001F50E Looking up your symptoms for context...")
        try:
            search_query = f"{user_input} near {user_location}"
            search_results = search_agent.run(search_query)
        except Exception as e:
            print(f"❌ Search failed: {e}")
            search_results = "No additional context available."

        print("\n\U0001F916 Generating follow-up questions...")
        try:
            followup_questions = followup_chain.run(user_input)
            print("\n❓ Follow-Up Questions:")
            print(followup_questions)
            followup_answers = input("\U0001F4DD Please answer the follow-up questions (combine all answers in one message): ").strip()
            if check_exit(followup_answers):
                print("\U0001F44B Exiting...")
                break
        except Exception as e:
            print(f"❌ Error generating follow-up questions: {e}")
            speak_text("Something went wrong while preparing your questions.")
            continue

        print("\n\U0001F916 Generating your diagnosis...")
        try:
            if previous_diagnosis and user_record:
                previous_symptoms = user_record[2]
                combined_input = combine_reports(previous_symptoms, previous_diagnosis, user_input, gender)
            else:
                combined_input = f"👤 Gender: {gender}\n{user_input}"

            diagnosis_response = symptom_chain.run({
                "input": combined_input,
                "search_results": search_results,
                "user_location": user_location,
                "followup_answers": followup_answers
            })
            diagnosis = speak_response(diagnosis_response)
            print(f"\n💬 Assistant Response:\n{diagnosis_response}")

        except Exception as e:
            print(f"\n❌ Error generating response: {e}")
            speak_text("There was an issue processing your symptoms. Please try again later.")
            continue

        if visited_before == "no" or is_new_user:
            print("✅ Saving to DB: ", name, user_input, user_id)
            save_user(name, user_input, user_location, diagnosis_response, user_id)
        else:
            print("✅ Updating DB for user:", user_id)
            update_user(user_id, user_input, user_location, diagnosis_response)

        print("✅ DB operation done, now checking critical...")

        lower_diag = diagnosis_response.lower()
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

        # 🩺 Offer Appointment Booking
        book_now = input("\n📅 Would you like to book an appointment with a doctor? (yes/no): ").strip().lower()
        if book_now in {"yes", "y"}:
            show_available_doctors()
            doctor_id = input("🆔 Enter Doctor ID to book: ").strip()
            slot = input("⏰ Enter preferred slot time (e.g., 10:00 AM): ").strip()
            result = book_appointment(doctor_id, slot)
            print("\n" + result)
            speak_text(result)

if __name__ == "__main__":
    main()