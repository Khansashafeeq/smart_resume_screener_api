from sqlalchemy import Column, Integer, String, Float
from database import Base
from pgvector.sqlalchemy import Vector

class Candidate(Base):
    __tablename__ = "candidates"
    id = Column(Integer, primary_key=True)
    name = Column(String)
    email = Column(String)
    skills = Column(String)
    experience = Column(Float)
    education = Column(String)
    embedding = Column(Vector(128)) 
