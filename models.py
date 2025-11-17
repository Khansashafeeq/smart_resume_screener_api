# models.py
from sqlalchemy import Column, Integer, String, Float
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import declarative_base
from database import Base

# try to import pgvector if installed
try:
    from pgvector.sqlalchemy import Vector
    HAVE_PGVECTOR = True
except Exception:
    Vector = None
    HAVE_PGVECTOR = False

class Candidate(Base):
    __tablename__ = "candidates"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255))
    email = Column(String(255), unique=True)
    skills = Column(JSONB, default=[])
    experience = Column(Float, default=0.0)
    education = Column(String, default="")

    if HAVE_PGVECTOR:
        embedding = Column(Vector(384))
    else:
        embedding = Column(JSONB, default=[])  # fallback storage as list
