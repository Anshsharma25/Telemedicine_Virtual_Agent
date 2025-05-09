import os
from langchain.agents import initialize_agent, AgentType
from langchain_openai import ChatOpenAI
from tools import (
    ai_doctor_api_tool,
    check_doctor_availability_tool,
    generate_meet_link_tool,
)

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

# Initialize OpenAI-based LLM for symptom diagnosis and doctor availability
llm = ChatOpenAI(
    model="mistralai/mistral-7b-instruct",  # Replace with any supported OpenRouter model
    base_url="https://openrouter.ai/api/v1",
    api_key=os.getenv("OPENROUTER_API_KEY"),
    temperature=0.7,
    max_tokens=512
)

# Symptom agent (diagnosis agent)
symptom_agent = initialize_agent(
    tools=[ai_doctor_api_tool],  # Tools to analyze symptoms (using AI Doctor API)
    llm=llm,
    agent_type=AgentType.CONVERSATIONAL_REACT_DESCRIPTION,
    verbose=True,  # For verbose output during agent execution
)

# Connect agent (availability + meet link generation)
connect_agent = initialize_agent(
    tools=[check_doctor_availability_tool, generate_meet_link_tool],  # Tools to check availability and generate meet links
    llm=llm,
    agent_type=AgentType.STRUCTURED_CHAT_ZERO_SHOT_REACT_DESCRIPTION,
    verbose=True,  # For verbose output during agent execution
)

# This script doesn't execute anything directly, it's meant to be imported by main.py
