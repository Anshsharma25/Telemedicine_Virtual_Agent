'''
+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
PHASE 1: Taking input from the user and passing it to the model in the form of a Text or audio.
+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
'''

import speech_recognition as sr
from langchain_google_genai import ChatGoogleGenerativeAI
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

# Initialize Gemini model
model = ChatGoogleGenerativeAI(model='gemini-1.5-pro')

# Function to capture audio input and convert to text
def capture_audio_input():
    recognizer = sr.Recognizer()
    microphone = sr.Microphone()
    print("Listening... Please speak.")

    with microphone as source:
        recognizer.adjust_for_ambient_noise(source)
        audio = recognizer.listen(source)

    try:
        # Recognize speech using Google Web Speech API
        text = recognizer.recognize_google(audio)
        print(f"Recognized Text: {text}")
        return text
    except sr.UnknownValueError:
        print("Sorry, I could not understand the audio.")
        return None
    except sr.RequestError:
        print("Could not request results; check your internet connection.")
        return None

# Main logic
def main():
    input_type = input("Enter input type (text/audio): ").strip().lower()

    if input_type == "text":
        user_input = input("Enter the Issue: ")
    elif input_type == "audio":
        user_input = capture_audio_input()
        if not user_input:
            print("No valid audio input detected.")
            return
    else:
        print("Invalid input type. Please enter 'text' or 'audio'.")
        return

    result = model.invoke(user_input)
    print("Model response:", result.content)

if __name__ == "__main__":
    main()
