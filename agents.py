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

# ──────────────────────────────── LLM Setup ─────────────────────────────────
llm = ChatOpenAI(
    model_name="mistralai/mistral-7b-instruct",
    openai_api_base="https://openrouter.ai/api/v1",
    openai_api_key=os.getenv("OPENROUTER_API_KEY"),
    temperature=0.7,
    max_tokens=1800,
)

# ─────────────────────────────── 🔁 NEW: Follow-up Question Generator ─────────────────────────────
followup_prompt = PromptTemplate(
    input_variables=["symptom"],
    template="""
You are an intelligent and empathetic medical assistant.

A patient described the following issue:
"{symptom}"

Before suggesting treatment, list 2 to 5 relevant follow-up questions a professional doctor would ask to better assess the situation.

Respond ONLY with the questions.
"""
)

followup_chain = LLMChain(llm=llm, prompt=followup_prompt, verbose=True)

# 🔁 Follow-up logic
def check_if_followup_needed(user_input: str, memory: dict):
    if "followup_answers" not in memory:
        questions = followup_chain.run(symptom=user_input)
        memory.update({
            "last_symptom": user_input,
            "pending_followup": True,
            "questions": questions
        })
        return False, questions
    else:
        return True, ""

# 🔁 Temporary memory for user sessions
memory = {}

# ───────────────────── Custom Prompt with Fixed Format ────────────────
PROMPT = PromptTemplate(
    input_variables=["input", "search_results", "user_location"],
    template="""
You are a highly capable and warm virtual medical assistant.

When a user describes their symptoms, ALWAYS respond in the following detailed 9-part format. Your goal is to sound professional yet human — providing **actionable**, **location-aware**, and **medically accurate** information with confidence.

Make sure your advice includes exact **dosage (mg), timing, frequency**, and **food-related instructions**. Do not skip any part.

1. 🦠 **Type of Disease & Injury**: Based on the followup_prompt just tell the name of disease/infection/injury or any think and tell why it happens?

2. 👨‍⚕️ **Doctor to Consult**: Suggest the most relevant doctor specialty (e.g., Dermatologist, Neurologist, ENT, General Physician). From this point onward, respond as that specialist with clarity, empathy, and precision.

3. 💊 **OTC Medicines & Immediate Remedies**: Include:
   - **Generic + Brand Name** (e.g., Paracetamol [Crocin])
   - **Dosage (e.g., 500mg)**, frequency, and **exact timing**
   - **Duration of intake**
   - **When to avoid**
   - Optional home remedies with usage frequency

4. 🛡️ **Preventive Measures**: What to avoid and maintain (e.g., no cold drinks, hydrate every 2 hours). Include timing/frequency.

5. 🥗 **Diet Recommendations**: 
   - What to **eat** and **why** it helps
   - What to **avoid** and **why**
   - Include fluids/supplements and how/when to take them

6. 🏠 **Additional Home Remedies**:
   - Use everyday items (e.g., turmeric, saltwater, eucalyptus oil)
   - Explain how and when to use each remedy in detail

7. 🧪 **Recommended Tests**:
   - Which tests (e.g., CBC, X-ray), **when** to take them
   - What they diagnose or rule out
   - Mark as **urgent** or **optional**

8. 📅 **Follow-Up Advice**:
   - Recovery time and when to see a doctor again
   - Mention any **red flag symptoms** that require emergency care

9. 📍 **Nearby Doctors, Hospitals, and Pharmacies**:
   - At least 1 **doctor** with name, specialty, hospital, hours, contact/book link
   - At least 1 **pharmacy** with name, address, hours, contact

ℹ️ If any web search was used, cite:
**Search reference:**
{search_results}

🧑‍⚕️ User said:
"{input}"

📍 Location:
{user_location}

Now generate a complete medical response covering all 9 sections.
"""
)

# ─────────────────────────────── Symptom Chain ─────────────────────────────
symptom_chain = LLMChain(
    llm=llm,
    prompt=PROMPT,
    verbose=True
)

# ───────────────────────────── Doctor Connection Agent ─────────────────────
connect_agent = initialize_agent(
    tools=[check_doctor_availability_tool, generate_meet_link_tool],
    llm=llm,
    agent_type=AgentType.STRUCTURED_CHAT_ZERO_SHOT_REACT_DESCRIPTION,
    handle_parsing_errors=True,
    verbose=True,
)

# ────────────────────────────── Medical Search Agent ───────────────────────
search_agent = initialize_agent(
    tools=[search_medical],
    llm=llm,
    agent_type=AgentType.STRUCTURED_CHAT_ZERO_SHOT_REACT_DESCRIPTION,
    handle_parsing_errors=True,
    verbose=True,
)