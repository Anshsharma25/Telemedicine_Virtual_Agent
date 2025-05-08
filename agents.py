from langchain.agents import AgentType
from langchain.agents import initialize_agent, AgentType

from langchain_google_genai import ChatGoogleGenerativeAI
from tools import (
    get_coordinates_tool,
    find_hospitals_tool,
    check_doctor_availability_tool,
    generate_meet_link_tool,
    send_meet_sms_tool
)


from dotenv import load_dotenv
import os

# Shared LLM
llm = ChatGoogleGenerativeAI(model="gemini-1.5-flash-latest")

# Agent 1: Symptom Intake Agent (No tools, just conversation)
symptom_agent = initialize_agent(
    tools=[],  # No tools used
    llm=llm,
    agent=AgentType.CONVERSATIONAL_REACT_DESCRIPTION,
    verbose=True,
)

# Agent 2: Hospital Finder Agent (Uses tools)
hospital_agent = initialize_agent(
    tools=[get_coordinates_tool, find_hospitals_tool],
    llm=llm,
    agent=AgentType.ZERO_SHOT_REACT_DESCRIPTION,
    verbose=True,
)

# Change the agent to ReActAgent
connect_agent = initialize_agent(
    tools=[check_doctor_availability_tool, generate_meet_link_tool, send_meet_sms_tool],
    llm=llm,
    agent=AgentType.STRUCTURED_CHAT_ZERO_SHOT_REACT_DESCRIPTION,
    verbose=True
)
