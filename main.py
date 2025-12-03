# main.py
import io
import os
import logging
from typing import List, Optional
from fastapi import FastAPI, UploadFile, File, Depends, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from sqlalchemy import or_, func, cast, String  # 👈 cast, String added
from sqlalchemy.exc import IntegrityError
from database import engine, Base, get_db
from models import Candidate
from resume_parser import parse_resume

# try optional embedding model
try:
    from sentence_transformers import SentenceTransformer
    EMB_MODEL = SentenceTransformer("all-MiniLM-L6-v2")
    def get_embedding(text: str) -> List[float]:
        vec = EMB_MODEL.encode(text).tolist()
        # ensure 384 size fallback if needed
        if len(vec) < 384:
            vec = vec + [0.0] * (384 - len(vec))
        return vec[:384]
    logging.info("SentenceTransformer loaded for embeddings.")
except Exception:
    EMB_MODEL = None
    def get_embedding(text: str) -> List[float]:
        # fallback zeros (safe)
        return [0.0] * 384
    logging.warning("sentence-transformers not available; using zero fallback embeddings.")

# try PDF reader
try:
    import PyPDF2
    def extract_text_from_pdf_bytes(b: bytes) -> str:
        reader = PyPDF2.PdfReader(io.BytesIO(b))
        pages = []
        for p in reader.pages:
            try:
                pages.append(p.extract_text() or "")
            except Exception:
                continue
        return "\n".join(pages).strip()
except Exception:
    # very light fallback: try decode
    def extract_text_from_pdf_bytes(b: bytes) -> str:
        try:
            return b.decode("utf-8", errors="ignore")
        except Exception:
            return ""

app = FastAPI(title="Smart Resume Screener (lite)", version="0.1")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# create tables if missing
Base.metadata.create_all(bind=engine)


@app.post("/upload")
async def upload_resume(file: UploadFile = File(...), db: Session = Depends(get_db)):
    # 1) read file bytes
    content = await file.read()
    if not content:
        raise HTTPException(status_code=400, detail="Empty file uploaded")

    # 2) extract text
    text = extract_text_from_pdf_bytes(content)
    if not text:
        raise HTTPException(
            status_code=400,
            detail="Could not extract text from PDF. Try a different file or check parser dependencies.",
        )

    # 3) parse resume
    details = parse_resume(text)
    email = details.get("email")
    if not email:
        raise HTTPException(status_code=400, detail="Could not detect email in resume")

    embedding = get_embedding(text)

    # 4) check if candidate already exists (same email)
    existing = db.query(Candidate).filter(Candidate.email == email).first()

    if existing:
        # ✅ UPDATE EXISTING
        existing.name = details.get("name") or existing.name
        existing.skills = details.get("skills") or existing.skills
        existing.experience = float(details.get("experience") or existing.experience or 0.0)
        existing.education = details.get("education") or existing.education
        existing.embedding = embedding or existing.embedding

        db.add(existing)
        db.commit()
        db.refresh(existing)

        return {
            "message": "Existing candidate updated",
            "id": existing.id,
            "name": existing.name,
            "email": existing.email,
            "skills": existing.skills,
            "experience": existing.experience,
        }

    # 5) CREATE NEW CANDIDATE
    cand = Candidate(
        name=details.get("name") or "Unknown",
        email=email,
        skills=details.get("skills") or [],
        experience=float(details.get("experience") or 0.0),
        education=details.get("education") or "",
        embedding=embedding,
    )
    db.add(cand)
    try:
        db.commit()
        db.refresh(cand)
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=400,
            detail="Candidate with this email already exists. Try again.",
        )

    return {
        "message": "New candidate created",
        "id": cand.id,
        "name": cand.name,
        "email": cand.email,
        "skills": cand.skills,
        "experience": cand.experience,
    }


@app.get("/search")
def search_candidates(
    query: str = Query(..., min_length=1),
    top: int = 5,
    db: Session = Depends(get_db),
):
    q = f"%{query}%"
    results = (
        db.query(Candidate)
        .filter(
            or_(
                Candidate.name.ilike(q),
                Candidate.email.ilike(q),
                cast(Candidate.skills, String).ilike(q),  # 👈 fixed cast here
            )
        )
        .limit(top)
        .all()
    )
    return [
        {
            "id": r.id,
            "name": r.name,
            "email": r.email,
            "skills": r.skills,
            "experience": r.experience,
        }
        for r in results
    ]


@app.get("/filter")
def filter_candidates(
    skill: Optional[str] = None,
    min_exp: float = 0.0,
    db: Session = Depends(get_db),
):
    q = db.query(Candidate)
    if skill:
        q = q.filter(
            cast(Candidate.skills, String).ilike(f"%{skill}%")  # 👈 fixed cast here
        )
    if min_exp:
        q = q.filter(Candidate.experience >= float(min_exp))
    rows = q.all()
    return [
        {
            "id": r.id,
            "name": r.name,
            "skills": r.skills,
            "experience": r.experience,
        }
        for r in rows
    ]


@app.get("/stats")
def stats(db: Session = Depends(get_db)):
    rows = db.query(Candidate).all()
    total = len(rows)
    avg_exp = sum((r.experience or 0.0) for r in rows) / total if total else 0.0
    skill_counts = {}
    for r in rows:
        for s in (r.skills or []):
            skill_counts[s] = skill_counts.get(s, 0) + 1
    top_skills = sorted(skill_counts.items(), key=lambda x: x[1], reverse=True)[:10]
    return {"total": total, "avg_experience": avg_exp, "top_skills": top_skills}
