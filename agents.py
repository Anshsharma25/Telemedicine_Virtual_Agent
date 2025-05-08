# Import necessary libraries and modules
import os
from langchain.agents import initialize_agent, AgentType
from langchain_google_genai import ChatGoogleGenerativeAI
from tools import ai_doctor_api_tool, get_coordinates_tool, find_hospitals_tool, check_doctor_availability_tool, generate_meet_link_tool, send_meet_sms_tool

# Shared LLM (Large Language Model) instance
llm = ChatGoogleGenerativeAI(model="gemini-1.5-flash-latest")

# Symptom Intake Agent (Diagnosis Agent)
symptom_agent = initialize_agent(
    tools=[ai_doctor_api_tool],
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


# Connect Agent (Doctor Connection Agent)
connect_agent = initialize_agent(
    tools=[check_doctor_availability_tool, generate_meet_link_tool, send_meet_sms_tool],
    llm=llm,
    agent=AgentType.STRUCTURED_CHAT_ZERO_SHOT_REACT_DESCRIPTION,
    verbose=True,
)
