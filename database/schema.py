# database/schema.py
import datetime
from sqlalchemy import (
    Column, Integer, String, Float, DateTime, Text, ForeignKey, JSON
)
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()

class Candidate(Base):
    __tablename__ = "candidates"

    id = Column(Integer, primary_key=True, autoincrement=True)
    full_name = Column(String(255), nullable=False, index=True)
    email = Column(String(255), nullable=True, index=True)
    phone_normalized = Column(String(20), nullable=False, unique=True, index=True)
    location = Column(String(100), nullable=True)
    experience_years = Column(Float, default=0.0)
    skills = Column(JSON, default=list)  # Normalized list of strings
    primary_source = Column(String(50), nullable=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

    # Relationships
    source_mappings = relationship("CandidateSourceMapping", back_populates="candidate", cascade="all, delete-orphan")
    audio_submissions = relationship("AudioSubmission", back_populates="candidate")

class CandidateSourceMapping(Base):
    __tablename__ = "candidate_source_mappings"

    id = Column(Integer, primary_key=True, autoincrement=True)
    candidate_id = Column(Integer, ForeignKey("candidates.id"), nullable=False)
    source_name = Column(String(50), nullable=False)  # source1, source2, source3
    original_identifier = Column(String(100), nullable=True)
    raw_payload = Column(JSON, nullable=False)

    candidate = relationship("Candidate", back_populates="source_mappings")

class AudioSubmission(Base):
    __tablename__ = "audio_submissions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    candidate_id = Column(Integer, ForeignKey("candidates.id"), nullable=True)
    applicant_name = Column(String(255), nullable=False)
    applicant_phone = Column(String(20), nullable=False)
    file_path = Column(String(500), nullable=False)
    file_name = Column(String(255), nullable=False)
    duration_seconds = Column(Float, nullable=False)
    sample_rate_khz = Column(Float, nullable=False)
    bitrate_kbps = Column(Float, nullable=False)
    loudness_db = Column(Float, nullable=False)
    snr_db = Column(Float, nullable=True)  # Signal-to-Noise Ratio (bonus metric)
    quality_flag = Column(String(50), default="Good")
    submitted_at = Column(DateTime, default=datetime.datetime.utcnow)

    candidate = relationship("Candidate", back_populates="audio_submissions")