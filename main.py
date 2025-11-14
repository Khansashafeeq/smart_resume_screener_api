from fastapi import FastAPI, File, UploadFile
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import List
import os
from dotenv import load_dotenv
from database import create_db, get_db
from models import Candidate
from resume_parser import parse_resume

load_dotenv()

app = FastAPI()

# Create database tables
@app.on_event("startup")
async def startup_event():
    create_db()

# Upload endpoint
@app.post("/upload")
async def upload_resume(file: UploadFile = File(...)):
    # Parse resume
    text = parse_resume(file.file)
    # Extract details
    details = extract_details(text)
    # Store in database
    db = get_db()
    candidate = Candidate(**details)
    db.add(candidate)
    db.commit()
    return JSONResponse(content={"message": "Resume uploaded successfully"}, status_code=200)

# Search endpoint
@app.get("/search")
async def search_candidates(query: str):
    # Get similar candidates
    db = get_db()
    candidates = db.query(Candidate).filter(Candidate.embedding.op('<->')(query)).limit(5).all()
    return JSONResponse(content=[candidate.to_dict() for candidate in candidates], status_code=200)

# Filter endpoint
@app.get("/filter")
async def filter_candidates(skill: str, min_exp: int):
    # Get filtered candidates
    db = get_db()
    candidates = db.query(Candidate).filter(Candidate.skills.contains(skill), Candidate.experience >= min_exp).all()
    return JSONResponse(content=[candidate.to_dict() for candidate in candidates], status_code=200)

# Stats endpoint
@app.get("/stats")
async def get_stats():
    # Get top skills, average experience, etc.
    db = get_db()
    top_skills = db.query(Candidate.skills).group_by(Candidate.skills).order_by(Candidate.skills.desc()).limit(5).all()
    avg_experience = db.query(Candidate.experience).avg()
    return JSONResponse(content={"top_skills": top_skills, "avg_experience": avg_experience}, status_code=200)
