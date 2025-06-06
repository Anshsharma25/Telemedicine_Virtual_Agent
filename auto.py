import pyautogui
import time
from pynput.keyboard import Controller, Key

keyboard = Controller()

while True:
    # Mouse move
    x, y = pyautogui.position()
    pyautogui.moveTo(x + 15, y + 15)
    time.sleep(1)
    pyautogui.moveTo(x, y)

    # Keyboard press (Shift key)
    keyboard.press(Key.shift)
    keyboard.release(Key.shift)

    # Wait for 60 seconds
    time.sleep(60)




from PyPDF2 import PdfReader
import requests

# Replace with your Gemini API key
GEMINI_API_KEY = "AIzaSyD6JlvM0jK6neRL_8GwIUakOBcr9GCWbuM"

def extract_pdf_text(path):
    reader = PdfReader(path)
    chunks = []
    for i, page in enumerate(reader.pages):
        text = page.extract_text()
        if text:
            chunks.append({"page": i + 1, "text": text})
    return chunks



def main(text):
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={GEMINI_API_KEY}"
    headers = {
        "Content-Type": "application/json"
    }
    hint = ("Please provide a concise and informative response based on the provided text and also provide the preventions.")
    input_text = f"instruction: {hint}\n\n{text}"
    # Prepare the request data
    data = {
        "contents": [{
            "parts": [{"text": input_text}],
        }]
    }
    response = requests.post(url, headers=headers, json=data)
    if response.status_code == 200:
        result = response.json()
        # Extract the relevant text from the response
        return result['candidates'][0]['content']['parts'][0]['text']
    else:
        return "Sorry, I couldn't process your request. Please try again."



if _name_ == "_main_":
    text = extract_pdf_text("sample.pdf")
    #print(text)
    #query = input("Enter your question: ")
    #text = query + "\n\n" + "\n".join([chunk['text'] for chunk in text])
    response = main(text)
    print("\nResponse from Gemini:\n")
    print(response)