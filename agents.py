# agents.py

import os
from dotenv import load_dotenv
from langchain.agents import initialize_agent, AgentType
from langchain.chat_models import ChatOpenAI
from tools import ai_doctor_api_tool, check_doctor_availability_tool, generate_meet_link_tool

load_dotenv()

# Instantiate LLM via OpenRouter endpoint
llm = ChatOpenAI(
    model_name="mistralai/mistral-7b-instruct",      # your Mistral instruct model
    openai_api_base="https://openrouter.ai/api/v1",   # OpenRouter proxy URL
    openai_api_key=os.getenv("OPENROUTER_API_KEY"),
    temperature=0.7,
    max_tokens=512
)

symptom_agent = initialize_agent(
    tools=[ai_doctor_api_tool],
    llm=llm,
    agent_type=AgentType.CONVERSATIONAL_REACT_DESCRIPTION,
    verbose=True,
)

connect_agent = initialize_agent(
    tools=[check_doctor_availability_tool, generate_meet_link_tool],
    llm=llm,
    agent_type=AgentType.STRUCTURED_CHAT_ZERO_SHOT_REACT_DESCRIPTION,
    verbose=True,
)
