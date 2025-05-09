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

