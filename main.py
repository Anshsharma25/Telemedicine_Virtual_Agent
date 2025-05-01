#this is the phase First taking the input from the user and then passing it to the model
from langchain_google_genai import ChatGoogleGenerativeAI
from dotenv import load_dotenv
load_dotenv()

model = ChatGoogleGenerativeAI(model= 'gemini-1.5-pro')

result = model.invoke("What is the capital of France?")
print(result.content)