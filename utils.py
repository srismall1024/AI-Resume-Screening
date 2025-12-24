import re, os
from PyPDF2 import PdfReader

def clean_text(text: str) -> str:
    text = text.lower()
    text = re.sub(r"[^a-z\s]", " ", text)
    return " ".join(text.split())

def extract_text_from_pdf(pdf_path: str) -> str:
    text = ""
    try:
        reader = PdfReader(pdf_path)
        for page in reader.pages:
            content = page.extract_text()
            if content: text += content + " "
    except Exception as e:
        print(f"Error reading {pdf_path}: {e}")
    return text