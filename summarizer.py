# summarizer.py
import os
import docx
from PyPDF2 import PdfReader
import openai

openai.api_key = os.getenv("OPENAI_API_KEY")

def extract_text(file_path):
    if file_path.endswith(".pdf"):
        reader = PdfReader(file_path)
        return " ".join([page.extract_text() for page in reader.pages if page.extract_text()])
    elif file_path.endswith(".docx"):
        doc = docx.Document(file_path)
        return " ".join([p.text for p in doc.paragraphs])
    return ""

def process_file(file_path):
    text = extract_text(file_path)
    if not text:
        return "No readable text found.", [], []

    prompt = f"""
    Summarize this academic project for a student defense.
    Provide:
    1. A short summary (3–5 sentences)
    2. Key points (bullet list)
    3. Possible defense questions
    Project text:\n{text}
    """

    response = openai.Completion.create(
        engine="text-davinci-003",
        prompt=prompt,
        max_tokens=500
    )

    output = response.choices[0].text.strip().split("\n")

    summary = " ".join(output[:3])
    key_points = output[3:8]
    questions = output[8:12]

    return summary, key_points, questions
