'''
+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
PHASE 1: Taking input from the user and passing it to the model in the form of Text or Audio.
+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
'''
import os
import requests
import speech_recognition as sr
import pyttsx3
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_community.tools import DuckDuckGoSearchResults

# Load environment variables
load_dotenv()
GOOGLE_MAPS_API_KEY = os.getenv("GOOGLE_MAPS_API_KEY")

# Initialize the Gemini model and text-to-speech engine
model = ChatGoogleGenerativeAI(model='gemini-1.5-flash-latest')

search_tool = DuckDuckGoSearchResults()
result = search_tool.run("what is happening in india today")
print(result)