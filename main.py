#this is the phase First taking the input from the user and then passing it to the model
'''
++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
PHASE 1: Taking input from the user and passing it to the model
++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
'''

from langchain_google_genai import ChatGoogleGenerativeAI
from dotenv import load_dotenv
load_dotenv()

model = ChatGoogleGenerativeAI(model= 'gemini-1.5-pro')

user = input("Enter the Issue: ")

result = model.invoke(user)
# print("Model response:")
print("Model response:" ,result.content)