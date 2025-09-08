# summarizer.py
from PyPDF2 import PdfReader
import docx
from openai import OpenAI
from config import OPENAI_API_KEY

client = OpenAI(api_key=OPENAI_API_KEY)

def extract_text(file_path):
    if file_path.endswith(".pdf"):
        reader = PdfReader(file_path)
        return " ".join([page.extract_text() or "" for page in reader.pages])
    elif file_path.endswith(".docx"):
        doc = docx.Document(file_path)
        return " ".join([p.text for p in doc.paragraphs])
    return ""

def process_file(file_path):
    text = extract_text(file_path)
    if not text.strip():
        return "No readable text found.", [], []

    # Call GPT
    response = client.chat.completions.create(
        model="gpt-4o-mini",   # Or "gpt-3.5-turbo"
        messages=[
            {"role": "system", "content": "You are a helpful assistant for academic project defense."},
            {"role": "user", "content": f"""
Summarize this academic project. Provide:
1. A short summary (3–5 sentences)
2. 5 key defense points
3. 5 possible examiner questions
Project text:\n{text[:4000]}
            """}
        ]
    )

    output = response.choices[0].message.content.strip()

    # Simple split (bot will format nicely)
    parts = output.split("\n")
    summary = "\n".join(parts[:3])
    key_points = [line for line in parts if line.strip().startswith("-")][:5]
    questions = [line for line in parts if "?" in line][:5]

    return summary, key_points, questions
