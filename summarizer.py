# summarizer.py
import os
import PyPDF2
from docx import Document
import openai

# Load OpenAI API key from environment
openai.api_key = os.environ.get("OPENAI_API_KEY")

def read_pdf(file_path):
    text = ""
    with open(file_path, "rb") as f:
        reader = PyPDF2.PdfReader(f)
        for page in reader.pages:
            text += page.extract_text() + "\n"
    return text

def read_docx(file_path):
    doc = Document(file_path)
    text = "\n".join([para.text for para in doc.paragraphs])
    return text

def summarize_text(text):
    prompt = (
        f"Summarize the following project content in a few paragraphs, "
        "list key points as bullet points, and provide 5 possible defense questions:\n\n"
        f"{text}"
    )
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[{"role":"user","content":prompt}],
        max_tokens=500
    )
    summary_text = response['choices'][0]['message']['content']
    
    # Split summary, key points, and questions (simple parsing)
    lines = summary_text.split("\n")
    summary, key_points, questions = [], [], []
    section = "summary"
    for line in lines:
        line = line.strip()
        if line.lower().startswith("key points") or line.startswith("🔑"):
            section = "key_points"
            continue
        elif line.lower().startswith("possible questions") or line.startswith("❓"):
            section = "questions"
            continue
        if section == "summary" and line:
            summary.append(line)
        elif section == "key_points" and line:
            key_points.append(line.strip("- ").strip())
        elif section == "questions" and line:
            questions.append(line.strip("- ").strip())
    
    return "\n".join(summary), key_points, questions

def process_file(file_path):
    ext = file_path.split(".")[-1].lower()
    if ext == "pdf":
        text = read_pdf(file_path)
    elif ext == "docx":
        text = read_docx(file_path)
    else:
        return "Unsupported file type.", [], []
    
    return summarize_text(text)
