# make_sample_resume_ali.py
# Simple script to generate a clean test resume PDF

from fpdf import FPDF

def create_resume_pdf(filename: str = "sample_resume_ali.pdf"):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=15)

    # Title
    pdf.set_font("Arial", "B", 18)
    pdf.cell(0, 10, "Ali Rehman", ln=True)
    pdf.set_font("Arial", "", 12)
    pdf.cell(0, 8, "Email: ali.rehman.dev@example.com", ln=True)
    pdf.cell(0, 8, "Location: Mumbai, India", ln=True)
    pdf.ln(5)

    # Summary
    pdf.set_font("Arial", "B", 14)
    pdf.cell(0, 8, "Summary", ln=True)
    pdf.set_font("Arial", "", 12)
    summary = (
        "Backend developer with 2+ years of hands-on experience in building APIs using Python, "
        "FastAPI, and PostgreSQL. Focused on clean architecture, performance, and automation."
    )
    pdf.multi_cell(0, 6, summary)
    pdf.ln(3)

    # Skills
    pdf.set_font("Arial", "B", 14)
    pdf.cell(0, 8, "Skills", ln=True)
    pdf.set_font("Arial", "", 12)
    skills = [
        "Python",
        "FastAPI",
        "PostgreSQL",
        "Docker",
        "Git",
        "Linux",
        "REST API Design",
    ]
    for s in skills:
        pdf.cell(0, 6, f"- {s}", ln=True)
    pdf.ln(3)

    # Experience
    pdf.set_font("Arial", "B", 14)
    pdf.cell(0, 8, "Experience", ln=True)
    pdf.set_font("Arial", "", 12)
    pdf.cell(0, 6, "Backend Developer – DemoTech Solutions (2022 - Present)", ln=True)
    exp_text = (
        "Worked on internal tools and automation systems using FastAPI and PostgreSQL. "
        "Implemented CRUD APIs, authentication, and background jobs for data processing."
    )
    pdf.multi_cell(0, 6, exp_text)
    pdf.ln(3)

    # Education
    pdf.set_font("Arial", "B", 14)
    pdf.cell(0, 8, "Education", ln=True)
    pdf.set_font("Arial", "", 12)
    pdf.multi_cell(0, 6, "Bachelor of Computer Applications (BCA)\nXYZ University, 2021")

    pdf.output(filename)
    print(f"Generated: {filename}")


if __name__ == "__main__":
    create_resume_pdf()
