import os
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain
from langchain.agents import initialize_agent, AgentType
from tools import (
    search_medical,
    check_doctor_availability_tool,
    generate_meet_link_tool,
)

load_dotenv()

# ─────────────────────────────────── LLM Setup ─────────────────────────────────────────────
llm = ChatOpenAI(
    model_name="mistralai/mistral-7b-instruct",
    openai_api_base="https://openrouter.ai/api/v1",
    openai_api_key=os.getenv("OPENROUTER_API_KEY"),
    temperature=0.7,
    max_tokens=512,
)

# ─────────────────────────────────── Custom Prompt ─────────────────────────────────────────
PROMPT = PromptTemplate(
    input_variables=["input", "search_results"],
    template="""
You are a helpful and knowledgeable virtual medical assistant.

When a user describes a symptom, ALWAYS respond in 3 parts:
1. Which medicine name to use (only over-the-counter or home remedies)
2. Preventive measures to avoid worsening or spreading
3. What to eat during this time to support recovery

If you looked up information, here are your search results:
{search_results}

Now, based on the user’s input and the search results above, provide your answer.

User symptoms: {input}
""".strip()
)

# ─────────────────────────────────── Symptom Chain ─────────────────────────────────────────
# This chain takes the symptom description and search results as inputs
symptom_chain = LLMChain(
    llm=llm,
    prompt=PROMPT,
    verbose=True
)

# ─────────────────────────────────── Doctor Connection Agent ───────────────────────────────
connect_agent = initialize_agent(
    tools=[check_doctor_availability_tool, generate_meet_link_tool],
    llm=llm,
    agent_type=AgentType.STRUCTURED_CHAT_ZERO_SHOT_REACT_DESCRIPTION,
    handle_parsing_errors=True,  # ← Add this line
    verbose=True,
)

# ─────────────────────────────────── Medical Search Agent ──────────────────────────────────
search_agent = initialize_agent(
    tools=[search_medical],
    llm=llm,
    agent_type=AgentType.STRUCTURED_CHAT_ZERO_SHOT_REACT_DESCRIPTION,
    handle_parsing_errors=True,
    verbose=True
)
