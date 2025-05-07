# speech_utils.py

import speech_recognition as sr
import pyttsx3

# Initialize text-to-speech engine
tts_engine = pyttsx3.init()

# Speak a given string using system voice
def speak_text(text):
    print("\n🗣️ Speaking the response...")
    tts_engine.say(text)
    tts_engine.runAndWait()

# Capture user's audio and convert it to text using Google's Speech Recognition
def capture_audio_input():
    recognizer = sr.Recognizer()
    mic = sr.Microphone()

    print("\n🎤 Listening... Please speak clearly.")
    with mic as source:
        recognizer.adjust_for_ambient_noise(source)
        audio = recognizer.listen(source)

    try:
        user_input = recognizer.recognize_google(audio)
        print(f"\n📝 Recognized Text: {user_input}")
        return user_input
    except sr.UnknownValueError:
        print("❌ Sorry, I could not understand the audio.")
    except sr.RequestError:
        print("❌ Could not reach Google servers. Please check your connection.")
    
    return None
