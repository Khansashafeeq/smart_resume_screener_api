from fpdf import FPDF

pdf = FPDF()
pdf.add_page()
pdf.set_font("Arial", size=12)

content = """
Name: Rahul Sharma
Email: rahul.sharma@example.com

Summary:
Detail-oriented backend developer with experience in Python, FastAPI, SQL, and Docker.
Strong understanding of API design, data modeling, and scalable backend architecture.

Skills:
Python
FastAPI
PostgreSQL
Docker
Git
Linux

Experience:
Worked on multiple backend automation tools.
1+ years experience in Python development.
"""

for line in content.split("\n"):
    pdf.cell(0, 10, txt=line, ln=True)

pdf.output("sample_resume_2.pdf")

print("sample_resume_2.pdf generated successfully!")
