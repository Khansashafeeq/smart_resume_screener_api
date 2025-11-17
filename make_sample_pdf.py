from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas

c = canvas.Canvas("sample_resume.pdf", pagesize=letter)
text = c.beginText(40, 700)
text.setFont("Helvetica", 12)
lines = [
 "John Doe",
 "Email: john@example.com",
 "",
 "Summary: Highly motivated backend developer with 2 years experience.",
 "",
 "Skills: Python, FastAPI, SQL, Docker"
]
for L in lines:
    text.textLine(L)
c.drawText(text)
c.save()
print("sample_resume.pdf created")
