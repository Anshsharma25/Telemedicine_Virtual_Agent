import os
from PyPDF2 import PdfReader
from dotenv import load_dotenv
from langchain.prompts import PromptTemplate
from langchain_core.runnables import RunnableSequence
from langchain_openai import ChatOpenAI
from langchain_core.messages import AIMessage

# ───────────── Load environment variables ─────────────
load_dotenv()

# ───────────── Setup LLM (Mistral via OpenRouter) ─────────────
llm = ChatOpenAI(
    model_name="mistralai/mistral-7b-instruct",
    openai_api_base="https://openrouter.ai/api/v1",
    openai_api_key=os.getenv("OPENROUTER_API_KEY"),
    temperature=0.7,
    max_tokens=1800
)

# ───────────── Prompt Template ─────────────
PDF_ANALYSIS_PROMPT = PromptTemplate(
    input_variables=["text"],
    template="""
You are a helpful medical assistant.

You will be given extracted text from a health-related PDF. Your job is to:

1. 🦠 **Precise Diagnosis or Injury & Explanation**: Identify the most likely condition and provide an exact medical reason (specific to India).

2. 📝 **Summarize the content concisely.**

3. 🛡️ **List any health-related advice or preventions mentioned or implied.**

4. 💡 **Provide actionable medical suggestions if appropriate.**

---

Text:
{text}

Now write a complete, clear medical explanation and prevention summary.
"""
)

# ───────────── Create Runnable Chain ─────────────
pdf_chain = PDF_ANALYSIS_PROMPT | llm

# ───────────── PDF Text Extraction ─────────────
def extract_pdf_text(path):
    reader = PdfReader(path)
    chunks = []
    for i, page in enumerate(reader.pages):
        text = page.extract_text()
        if text:
            chunks.append(text)
    return "\n".join(chunks)

# ───────────── Main Document Processor ─────────────
def maindocument(file_path):
    if not file_path.lower().endswith(".pdf"):
        print("❌ Please provide a valid PDF file.")
        return ""

    try:
        print("\n🔍 Extracting text...")
        combined_text = extract_pdf_text(file_path)
        if not combined_text.strip():
            print("❌ No text found in the PDF.")
            return ""

        print("\n🤖 Processing with LLM...\n")
        response = pdf_chain.invoke({"text": combined_text})
        print("🧠 LLM Response:\n")
        print(response.content if hasattr(response, "content") else response)

        # Return the response content back to main.py
        if hasattr(response, "content"):
            return response.content.strip()
        elif isinstance(response, AIMessage):
            return response.content
        else:
            return str(response)

    except Exception as e:
        print(f"❌ Failed to process the file: {e}")
        return ""

# ───────────── Debug Run ─────────────
if __name__ == "__main__":
    sample_path = input("📄 Enter PDF file path: ").strip()
    summary = maindocument(sample_path)
    if summary:
        print("\n✅ Final Output to main.py:\n")
        print(summary)
