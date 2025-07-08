# ─── agent.py ─────────────────────────────────────────────────────────────
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

llm = ChatOpenAI(
    model_name="mistralai/mistral-7b-instruct",
    openai_api_base="https://openrouter.ai/api/v1",
    openai_api_key=os.getenv("OPENROUTER_API_KEY"),
    temperature=0.7,
    max_tokens=1800,
)

# Follow-up question prompt
FOLLOWUP_PROMPT = PromptTemplate(
    input_variables=["input"],
    template="""
You are a skilled virtual health assistant. Based on the user's initial symptom input, ask 3 medically relevant and focused **follow-up questions** that will help **narrow down the diagnosis**.

Do **not** suggest any diagnosis, medicines, or treatment yet.

User Input:
"{input}"

---

❓ Follow-up Questions:
1.
2.
3.
"""
)

followup_chain = LLMChain(
    llm=llm,
    prompt=FOLLOWUP_PROMPT,
    verbose=True
)

# Final diagnosis prompt
FINAL_PROMPT = PromptTemplate(
    input_variables=["input", "followup_answers", "search_results", "user_location"],
    template="""
You are a highly skilled and warm virtual medical assistant.

Your job is to give precise, medical responses based on user symptoms. Follow these steps *strictly*:

1. Ask *1 to 3 highly focused follow-up questions* to clarify symptoms. Do not ask general questions. Only ask questions that directly help *narrow down the most likely diagnosis*.

2. Then, using clinical reasoning, give *only one most likely diagnosis or condition*. 
   - You must *not* list multiple possibilities unless explaining clearly *why* the selected one is more likely than others.
   - Avoid general terms like "viral infection", "flu-like symptoms", or "many causes".

3. Finally, follow the format below and include *accurate mg dosage, frequency, timing, food interaction, and usage limitations* for each medicine or remedy.

---

👤 Initial User Input:
{input}

🧠 Follow-up Answers:
{followup_answers}

📍 Location:
{user_location}

---

1. 🦠 *Precise Diagnosis or Injury & Explanation*: [Most likely condition, exact medical reason] in India.

2. 👨‍⚕ *Doctor to Consult: Recommend the **exact specialty* the user should consult (e.g., Neurologist, ENT). Then speak as that doctor going forward with clear and confident instructions.

3. 💊 **OTC Medicines & Immediate Remedies based on Diagnosis **: 
   - Include *Generic Name + Brand Name + Price (in INR)*  
   - Give *Dosage (e.g., 500mg), Frequency (e.g., every 6 hrs), Duration (e.g., 3 days)*
   - Mention *whether to take with or without food*
   - List any *conditions when it should be avoided*
   - Optional: List *1–2 home remedies* with timing

4. 🗁 *Preventive Measures based on Diagnosis*:
   - What to *avoid*
   - What to *maintain/do, including exact **frequency/timing*

5. 🥗 *Diet Recommendations  based on Diagnosis*:
   - What to *eat*, how it helps
   - What to *avoid*, and why
   - Include relevant *fluids/supplements*, when/how to take

6. 🏠 *Additional Home Remedies based on Diagnosis*:
   - Recommend easy remedies using everyday items
   - Explain *how, when, and how often* to use them

7. 🦪 *Recommended Tests based on Diagnosis*:
   - Clearly list required tests (e.g., CBC, ESR, X-ray)
   - Mark as *Urgent* or *Optional*
   - Explain *what each test will confirm or rule out*

8. 🗕 *Follow-Up Advice*:
   - When to expect recovery
   - When to seek in-person consultation
   - Mention *red flag symptoms* that need urgent care

9. 📍 *Nearby Doctors, Hospitals, and Pharmacies*:
   - Give *1 nearby doctor* (name, specialty, hospital, hours, contact link , Fee for per patient)
   - Give *1 nearby doctor clinic* (name, specialty, clinic address, hours, contact number , Fee for per patient)
   - Give *1 nearby pharmacy* (name, address, hours, phone)

️ Search Reference:
{search_results}
"""
)

symptom_chain = LLMChain(
    llm=llm,
    prompt=FINAL_PROMPT,
    verbose=True
)

connect_agent = initialize_agent(
    tools=[check_doctor_availability_tool, generate_meet_link_tool],
    llm=llm,
    agent_type=AgentType.STRUCTURED_CHAT_ZERO_SHOT_REACT_DESCRIPTION,
    handle_parsing_errors=True,
    verbose=True,
)

search_agent = initialize_agent(
    tools=[search_medical],
    llm=llm,
    agent_type=AgentType.STRUCTURED_CHAT_ZERO_SHOT_REACT_DESCRIPTION,
    handle_parsing_errors=True,
    verbose=True,
)

__all__ = ["symptom_chain", "followup_chain", "connect_agent", "search_agent"]
