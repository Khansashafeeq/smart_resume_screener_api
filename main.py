# main.py
import io
import os
import logging
from typing import List, Optional
from fastapi import FastAPI, UploadFile, File, Depends, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from sqlalchemy import or_, func
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
    # read file bytes
    content = await file.read()
    if not content:
        raise HTTPException(status_code=400, detail="Empty file uploaded")

    # try to extract text
    text = extract_text_from_pdf_bytes(content)
    if not text:
        raise HTTPException(status_code=400, detail="Could not extract text from PDF. Try a different file or check parser dependencies.")

    # parse resume
    details = parse_resume(text)
    embedding = get_embedding(text)

    # insert into DB
    cand = Candidate(
        name=details.get("name") or "Unknown",
        email=details.get("email"),
        skills=details.get("skills") or [],
        experience=float(details.get("experience") or 0.0),
        education=details.get("education") or "",
        embedding=embedding  # if pgvector installed, this stores vector; otherwise a list will try to be stored
    )
    db.add(cand)
    db.commit()
    db.refresh(cand)

    return {"id": cand.id, "name": cand.name, "email": cand.email, "skills": cand.skills, "experience": cand.experience}

@app.get("/search")
def search_candidates(query: str = Query(..., min_length=1), top: int = 5, db: Session = Depends(get_db)):
    q = f"%{query}%"
    # basic search by name/email or skill text
    results = db.query(Candidate).filter(
        or_(
            Candidate.name.ilike(q),
            Candidate.email.ilike(q),
            func.cast(Candidate.skills, type_=func.text).ilike(q)
        )
    ).limit(top).all()
    return [{"id": r.id, "name": r.name, "email": r.email, "skills": r.skills, "experience": r.experience} for r in results]

@app.get("/filter")
def filter_candidates(skill: Optional[str] = None, min_exp: float = 0.0, db: Session = Depends(get_db)):
    q = db.query(Candidate)
    if skill:
        # JSONB contains sometimes works; fallback to text match
        q = q.filter(func.cast(Candidate.skills, type_=func.text).ilike(f"%{skill}%"))
    if min_exp:
        q = q.filter(Candidate.experience >= float(min_exp))
    rows = q.all()
    return [{"id": r.id, "name": r.name, "skills": r.skills, "experience": r.experience} for r in rows]

@app.get("/stats")
def stats(db: Session = Depends(get_db)):
    rows = db.query(Candidate).all()
    total = len(rows)
    avg_exp = sum((r.experience or 0.0) for r in rows) / total if total else 0.0
    # top skills simple count
    skill_counts = {}
    for r in rows:
        for s in (r.skills or []):
            skill_counts[s] = skill_counts.get(s, 0) + 1
    top_skills = sorted(skill_counts.items(), key=lambda x: x[1], reverse=True)[:10]
    return {"total": total, "avg_experience": avg_exp, "top_skills": top_skills}
