import re

def parse_resume(text: str):
    name = "Unknown"
    email = None
    skills = []
    experience = 0
    education = "Auto-detected education"

    email_match = re.search(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}", text)
    if email_match:
        email = email_match.group(0)

    skill_keywords = ["python", "fastapi", "sql", "docker", "ml", "ai"]
    skills = [s for s in skill_keywords if s in text.lower()]

    exp_match = re.search(r"(\d+)\s+years", text.lower())
    if exp_match:
        experience = int(exp_match.group(1))

    first_line = text.strip().split("\n")[0]
    name = first_line[:60]

    return {
        "name": name,
        "email": email,
        "skills": skills,
        "experience": experience,
        "education": education
    }
