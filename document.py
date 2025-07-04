import os
from PyPDF2 import PdfReader
from docx import Document
from dotenv import load_dotenv
from paddleocr import PaddleOCR
from langchain.prompts import PromptTemplate
from langchain_core.runnables import RunnableSequence
from langchain_openai import ChatOpenAI
from langchain_core.messages import AIMessage
from PIL import Image

# ───────────── Resize Image Utility ─────────────
def resize_image(path, max_width=1000):
    img = Image.open(path)
    if img.width > max_width:
        ratio = max_width / img.width
        new_size = (max_width, int(img.height * ratio))
        img = img.resize(new_size)
        new_path = path.replace(".jpg", "_resized.jpg").replace(".jpeg", "_resized.jpeg").replace(".png", "_resized.png")
        img.save(new_path)
        return new_path
    return path

def cleanup_temp_image(path):
    if "_resized" in path and os.path.exists(path):
        os.remove(path)

# ───────────── Load environment variables ─────────────
load_dotenv()

# ───────────── Initialize OCR ─────────────
ocr = PaddleOCR(use_textline_orientation=True, lang='en')

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

You will be given extracted text from a health-related document. Your job is to:

1. 🦠 *Precise Diagnosis or Injury & Explanation*: Identify the most likely condition and provide an exact medical reason (specific to India).
2. 📝 *Summarize the content concisely.*
3. 🛡 *List any health-related advice or preventions mentioned or implied.*
4. 💡 *Provide actionable medical suggestions if appropriate.*

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
    for page in reader.pages:
        text = page.extract_text()
        if text:
            chunks.append(text)
    return "\n".join(chunks)

# ───────────── DOCX Text Extraction ─────────────
def extract_docx_text(path):
    doc = Document(path)
    return "\n".join([para.text for para in doc.paragraphs if para.text.strip()])

# ───────────── Image Text Extraction using PaddleOCR ─────────────
def extract_image_text(path):
    print("🖼 Running OCR on image...")

    resized_path = resize_image(path)

    result = ocr.predict(resized_path)
    print("✅ OCR completed.")

    texts = []
    for line in result:
        for word_info in line:
            texts.append(word_info[1][0])
    print("📝 Text extracted from image:\n", "\n".join(texts[:5]), "...")

    cleanup_temp_image(resized_path)
    return "\n".join(texts)

# ───────────── Main Document Processor ─────────────
def maindocument(file_path):
    file_path = file_path.strip()
    text = ""

    if not os.path.exists(file_path):
        print("❌ File not found.")
        return ""

    ext = os.path.splitext(file_path)[1].lower()

    try:
        print("\n🔍 Extracting text...")

        if ext == ".pdf":
            text = extract_pdf_text(file_path)
        elif ext in [".docx"]:
            text = extract_docx_text(file_path)
        elif ext in [".jpg", ".jpeg", ".png", ".bmp"]:
            text = extract_image_text(file_path)
        else:
            print("❌ Unsupported file format.")
            return ""

        if not text.strip():
            print("❌ No text found in the file.")
            return ""

        print("\n🤖 Processing with LLM...\n")
        response = pdf_chain.invoke({"text": text})
        print("🧠 LLM Response:\n")

        output = response.content if hasattr(response, "content") else str(response)
        print(output)
        return output

    except Exception as e:
        print(f"❌ Failed to process the file: {e}")
        return ""

# ───────────── Debug Run ─────────────
if __name__ == "__main__":
    sample_path = input("📄 Enter file path (PDF/DOCX/Image): ")
    summary = maindocument(sample_path)
    if summary:
        print("\n✅ Final Output:\n")
        print(summary)