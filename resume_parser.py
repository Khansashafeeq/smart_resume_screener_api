import PyPDF2
from io import BytesIO

def parse_resume(file):
    pdf_file = BytesIO(file.read())
    pdf_reader = PyPDF2.PdfReader(pdf_file)
    text = ""
    for page in pdf_reader.pages:
        text += page.extract_text()
    return text
