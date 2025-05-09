<<<<<<< HEAD
import requests
import googlemaps # type: ignore

# Replace with your Google API Key
GOOGLE_API_KEY = "AIzaSyCVQNuIoyvSAMJL24Pu6ZI7r3zK2DKAZNo"

# Initialize the Google Maps clientS
gmaps = googlemaps.Client(key=GOOGLE_API_KEY)

# Function to get latitude and longitude from an address
def get_coordinates(address):
    geocode_result = gmaps.geocode(address)
    if geocode_result:
        lat = geocode_result[0]['geometry']['location']['lat']
        lng = geocode_result[0]['geometry']['location']['lng']
        print(f"Coordinates for {address}: Latitude = {lat}, Longitude = {lng}")
        return lat, lng
    else:
        print("Address not found.")
        return None, None

# Function to find nearby hospitals
def find_nearby_hospitals(lat, lng, radius=5000):
    url = f"https://maps.googleapis.com/maps/api/place/nearbysearch/json?location={lat},{lng}&radius={radius}&type=hospital&key={GOOGLE_API_KEY}"
    response = requests.get(url)
    data = response.json()

    if data.get("status") == "OK":
        hospitals = data.get("results", [])
        for i, hospital in enumerate(hospitals[:5]):  # Get top 5 hospitals
            name = hospital.get("name")
            address = hospital.get("vicinity")
            rating = hospital.get("rating", "N/A")
            print(f"{i + 1}. {name} | Rating: {rating} | Address: {address}")
    else:
        print("No hospitals found nearby.")

# Example: Provide an address and get nearby hospitals
address = "Sector 132, Noida, Uttar Pradesh, India"
lat, lng = get_coordinates(address)

if lat and lng:
    find_nearby_hospitals(lat, lng)
=======
# '''
# +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
# PHASE 1: Taking input from the user and passing it to the model in the form of Text or Audio.
# +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
# '''
# import os
# import requests
# import speech_recognition as sr
# import pyttsx3
# from dotenv import load_dotenv
# from langchain_google_genai import ChatGoogleGenerativeAI
# from langchain_community.tools import DuckDuckGoSearchResults

# # Load environment variables
# load_dotenv()
# GOOGLE_MAPS_API_KEY = os.getenv("GOOGLE_MAPS_API_KEY")

# # Initialize the Gemini model and text-to-speech engine
# model = ChatGoogleGenerativeAI(model='gemini-1.5-flash-latest')

# search_tool = DuckDuckGoSearchResults()
# result = search_tool.run("what is happening in india today")
# print(result)

import os
from dotenv import load_dotenv
from langchain_huggingface import HuggingFaceEndpoint  # Import from langchain-huggingface
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain

# Load environment variables from the .env file
load_dotenv()

# Get the API token and model name from environment variables
huggingface_api_token = os.getenv("HUGGINGFACE_API_TOKEN")
model_name = os.getenv("HUGGINGFACE_MODEL_NAME")

# Initialize HuggingFaceEndpoint with repo_id and model_kwargs
hf_endpoint = HuggingFaceEndpoint(
    repo_id=model_name,  # Correctly pass repo_id directly
    hf_token=huggingface_api_token,  # Provide the API token directly
    model_kwargs={"max_length": 150}  # You can specify other parameters here
)

# Create a prompt template (you can customize it based on the user's input)
prompt = "You have a user describing symptoms: {symptoms}. What do you recommend?"

# Initialize the prompt template and chain
prompt_template = PromptTemplate(input_variables=["symptoms"], template=prompt)
llm_chain = LLMChain(llm=hf_endpoint, prompt=prompt_template)

# Function to handle user input
def handle_user_input(user_input):
    # Call the model with the user input
    response = llm_chain.run({"symptoms": user_input})
    return response

# Example of user input
user_input = input("Enter symptoms (e.g., headache, arm pain): ")

# Get response from Hugging Face model
response = handle_user_input(user_input)
print(f"AI Response: {response}")

>>>>>>> origin/Agentic_Ai
