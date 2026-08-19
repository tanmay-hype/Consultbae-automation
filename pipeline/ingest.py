# pipeline/ingest.py
import pandas as pd
import json
from sqlalchemy.orm import Session
from database.connection import engine, SessionLocal
from database.schema import Base, Candidate, CandidateSourceMapping
from pipeline.normalizer import (
    normalize_phone, normalize_email, normalize_name, parse_experience, normalize_skills
)
from pipeline.matcher import resolve_candidate

def run_ingestion_pipeline():
    Base.metadata.create_all(bind=engine)
    db: Session = SessionLocal()

    sources = [
        {"name": "source1_naukri", "path": "data/source1_naukri_applicants.csv"},
        {"name": "source2_gig_workers", "path": "data/source2_gig_workers.csv"},
        {"name": "source3_cbnexus", "path": "data/source3_cbnexus_contacts.csv"}
    ]

    for src in sources:
        print(f"[*] Processing {src['name']}...")
        df = pd.read_csv(src["path"])
        
        for _, row in df.iterrows():
            row_dict = row.to_dict()
            
            # Field extraction across schemas
            raw_name = row_dict.get("name") or row_dict.get("full_name") or row_dict.get("candidate_name")
            raw_phone = row_dict.get("phone") or row_dict.get("contact") or row_dict.get("mobile")
            raw_email = row_dict.get("email") or row_dict.get("mail_id")
            raw_exp = row_dict.get("experience") or row_dict.get("exp") or row_dict.get("work_experience")
            raw_skills = row_dict.get("skills") or row_dict.get("skillset") or row_dict.get("primary_skills")
            raw_loc = row_dict.get("location") or row_dict.get("city")

            phone_norm = normalize_phone(raw_phone)
            if not phone_norm:
                continue  # Skip unidentifiable records without valid contact numbers

            email_norm = normalize_email(raw_email)
            name_norm = normalize_name(raw_name)
            exp_years = parse_experience(raw_exp)
            skills_list = normalize_skills(raw_skills)

            # Query existing candidate records
            existing_candidates = [
                {
                    "id": c.id,
                    "full_name": c.full_name,
                    "email": c.email,
                    "phone_normalized": c.phone_normalized,
                    "location": c.location,
                    "skills": c.skills,
                    "experience_years": c.experience_years
                }
                for c in db.query(Candidate).all()
            ]

            incoming_payload = {
                "full_name": name_norm,
                "email": email_norm,
                "phone_normalized": phone_norm,
                "location": str(raw_loc).strip() if pd.notna(raw_loc) else None
            }

            matched_id = resolve_candidate(incoming_payload, existing_candidates)

            if matched_id:
                # Merge logic: Union skills, take max experience, backfill missing email/location
                candidate = db.query(Candidate).filter(Candidate.id == matched_id).first()
                candidate.skills = sorted(list(set(candidate.skills + skills_list)))
                candidate.experience_years = max(candidate.experience_years, exp_years)
                if not candidate.email and email_norm:
                    candidate.email = email_norm
                if not candidate.location and incoming_payload["location"]:
                    candidate.location = incoming_payload["location"]
            else:
                # Insert novel candidate record
                candidate = Candidate(
                    full_name=name_norm,
                    email=email_norm,
                    phone_normalized=phone_norm,
                    location=incoming_payload["location"],
                    experience_years=exp_years,
                    skills=skills_list,
                    primary_source=src["name"]
                )
                db.add(candidate)
                db.flush()

            # Record audit mapping
            audit_entry = CandidateSourceMapping(
                candidate_id=candidate.id,
                source_name=src["name"],
                original_identifier=str(row_dict.get("id") or row_dict.get("applicant_id") or ""),
                raw_payload=json.loads(json.dumps(row_dict, default=str))
            )
            db.add(audit_entry)

        db.commit()
    print("[+] Ingestion & Deduplication complete.")

if __name__ == "__main__":
    run_ingestion_pipeline()