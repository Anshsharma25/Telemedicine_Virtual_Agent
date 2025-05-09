import os
from langchain.agents import initialize_agent, AgentType
from langchain_google_genai import ChatGoogleGenerativeAI
from tools import (
    ai_doctor_api_tool,
    check_doctor_availability_tool,
    generate_meet_link_tool,
)

# LLM setup
llm = ChatGoogleGenerativeAI(model="gemini-1.5-flash-latest")

# Symptom agent (diagnosis)
symptom_agent = initialize_agent(
    tools=[ai_doctor_api_tool],
    llm=llm,
    agent_type=AgentType.CONVERSATIONAL_REACT_DESCRIPTION,
    verbose=True,
)

# Connect agent (availability + meet link)
connect_agent = initialize_agent(
    tools=[check_doctor_availability_tool, generate_meet_link_tool],
    llm=llm,
    agent_type=AgentType.STRUCTURED_CHAT_ZERO_SHOT_REACT_DESCRIPTION,
    verbose=True,
)
