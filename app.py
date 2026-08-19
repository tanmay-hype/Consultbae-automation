# app.py
import os
import shutil
from fastapi import FastAPI, Request, UploadFile, File, Form, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from database.connection import engine, SessionLocal
from database.schema import Base, Candidate, AudioSubmission
from pipeline.normalizer import normalize_phone, normalize_name
from audio_engine.processor import analyze_audio_file

app = FastAPI(title="ConsultBae Audio Collection Engine")

os.makedirs("data/uploads", exist_ok=True)
app.mount("/static", StaticFiles(directory="web/static"), name="static")
app.mount("/uploads", StaticFiles(directory="data/uploads"), name="uploads")
templates = Jinja2Templates(directory="web/templates")

Base.metadata.create_all(bind=engine)

@app.get("/", response_class=HTMLResponse)
def serve_index(request: Request):
    db = SessionLocal()
    submissions = db.query(AudioSubmission).order_by(AudioSubmission.submitted_at.desc()).all()
    db.close()
    return templates.TemplateResponse("index.html", {"request": request, "submissions": submissions})

@app.post("/api/submit-audio")
async def handle_audio_submission(
    applicant_name: str = Form(...),
    applicant_phone: str = Form(...),
    audio_file: UploadFile = File(...)
):
    phone_norm = normalize_phone(applicant_phone)
    if not phone_norm:
        raise HTTPException(status_code=400, detail="Invalid 10-digit mobile number.")
    
    clean_name = normalize_name(applicant_name)
    
    # Save file to disk
    file_location = f"data/uploads/{phone_norm}_{audio_file.filename}"
    with open(file_location, "wb") as buffer:
        shutil.copyfileobj(audio_file.file, buffer)
        
    # Analyze DSP properties
    metrics = analyze_audio_file(file_location)
    
    db = SessionLocal()
    # Link to existing Candidate from Task 1 if available
    matched_candidate = db.query(Candidate).filter(Candidate.phone_normalized == phone_norm).first()
    
    submission = AudioSubmission(
        candidate_id=matched_candidate.id if matched_candidate else None,
        applicant_name=clean_name,
        applicant_phone=phone_norm,
        file_path=file_location,
        file_name=f"/uploads/{phone_norm}_{audio_file.filename}",
        duration_seconds=metrics["duration_seconds"],
        sample_rate_khz=metrics["sample_rate_khz"],
        bitrate_kbps=metrics["bitrate_kbps"],
        loudness_db=metrics["loudness_db"],
        snr_db=metrics["snr_db"],
        quality_flag=metrics["quality_flag"]
    )
    db.add(submission)
    db.commit()
    db.refresh(submission)
    db.close()
    
    return JSONResponse(content={"status": "success", "metrics": metrics})

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=True)