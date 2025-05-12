# agents.py

import os
from dotenv import load_dotenv

# Use the community OpenAI import to avoid deprecation
from langchain_community.chat_models import ChatOpenAI
from langchain.chains import LLMChain
from langchain.prompts import PromptTemplate

from tools import search_tool, check_doctor_availability_tool, generate_meet_link_tool

load_dotenv()

# ─── LLM Setup ─────────────────────────────────────────────────────────────────
llm = ChatOpenAI(
    model_name="mistralai/mistral-7b-instruct",
    openai_api_base="https://openrouter.ai/api/v1",
    openai_api_key=os.getenv("OPENROUTER_API_KEY"),
    temperature=0.7,
    max_tokens=512,
)

# ─── Custom Prompt: 3-Point Structure + Search Context ──────────────────────────
PROMPT = PromptTemplate(
    input_variables=["input", "search_results"],
    template="""
You are a helpful and knowledgeable virtual medical assistant.

When a user describes a symptom, ALWAYS respond in 3 parts:
1. Which medicine to use (only over-the-counter or home remedies)
2. Preventive measures to avoid worsening or spreading
3. What to eat during this time to support recovery

If you looked up information, here are your search results:
{search_results}

Now, based on the user’s input and the search results above, provide your answer.

User symptoms: {input}
""".strip()
)

# ─── The chain that does the work ──────────────────────────────────────────────
symptom_chain = LLMChain(
    llm=llm,
    prompt=PROMPT,
    verbose=True
)

# ─── Existing doctor-connect agent stays the same ─────────────────────────────
from langchain.agents import initialize_agent, AgentType

connect_agent = initialize_agent(
    tools=[check_doctor_availability_tool, generate_meet_link_tool],
    llm=llm,
    agent_type=AgentType.STRUCTURED_CHAT_ZERO_SHOT_REACT_DESCRIPTION,
    verbose=True,
)
