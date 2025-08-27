# import openai

# openai.api_key = "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"
# openai.api_base = "https://openrouter.ai/api/v1"

# # Initial system message
# messages = [
#     {"role": "system", "content": "You are a helpful medical assistant."}
# ]

# while True:
#     user_input = input("User: ")
    
#     if user_input.lower() in ["exit", "quit"]:
#         print("Exiting chat.")
#         break

#     messages.append({"role": "user", "content": user_input})

#     response = openai.ChatCompletion.create(
#         model="mistralai/mistral-7b-instruct",
#         messages=messages
#     )

#     assistant_reply = response['choices'][0]['message']['content']
#     messages.append({"role": "assistant", "content": assistant_reply})

#     print(f"Assistant: {assistant_reply}\n")





import pyttsx3
import speech_recognition as sr
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage

# 🚨 Your Gemini API Key here (DO NOT share publicly)
GOOGLE_API_KEY = "AIzaSyDa5bshKvo1RfhV0dvOpbLPdjPr6bcavGA"  # Replace this with your actual key

# 🔊 Text-to-Speech setup
engine = pyttsx3.init()
engine.setProperty("rate", 150)  # speed
voices = engine.getProperty("voices")

# Select a voice that sounds more natural in English
for voice in voices:
    if "female" in voice.name.lower() or "zira" in voice.id.lower():
        engine.setProperty("voice", voice.id)
        break

def speak(text):
    print(f"\n🤖 AI (in English): {text}")
    engine.say(text)
    engine.runAndWait()

# 🎙️ Speech Recognition setup
def listen():
    recognizer = sr.Recognizer()
    with sr.Microphone() as source:
        print("\n🎙️ Listening (speak in Hindi)...")
        recognizer.adjust_for_ambient_noise(source)
        audio = recognizer.listen(source)
    try:
        text = recognizer.recognize_google(audio, language="hi-IN")
        print(f"🗣️ You said (Hindi): {text}")
        return text
    except sr.UnknownValueError:
        speak("Sorry, I didn't understand. Please try again.")
        return None
    except sr.RequestError:
        speak("Network error. Try again later.")
        return None

# 🤖 Gemini LLM setup
llm = ChatGoogleGenerativeAI(model="gemini-pro", google_api_key=GOOGLE_API_KEY)

# 🔁 Chat Loop
def chat_loop():
    speak("Hello! I'm your Gemini assistant. Ask me anything in Hindi.")
    while True:
        user_input = listen()
        if not user_input:
            continue
        if user_input.lower() in ["band karo", "exit", "stop", "bye"]:
            speak("Thank you! Goodbye.")
            break
        try:
            # Translate + answer in English
            prompt = f"Translate the following Hindi question into English and answer it in English: {user_input}"
            response = llm.invoke([HumanMessage(content=prompt)])
            speak(response.content)
        except Exception as e:
            print("⚠️ Error:", e)
            speak("Something went wrong. Please try again.")

# 🚀 Run the assistant
if __name__ == "__main__":
    chat_loop()
