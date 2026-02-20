from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
from fastapi import APIRouter, File, UploadFile, HTTPException, Depends
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.db.models import Job, Material, JobStatus
import shutil
import os
from tempfile import NamedTemporaryFile
from stl import mesh

router = APIRouter()

# --- Pydantic Schemas (DTOs) ---
class QuoteRequest(BaseModel):
    filename: str
    material: str
    quantity: int

class QuoteResponse(BaseModel):
    volume_cm3: float
    weight_g: float
    total_cost: float
    currency: str

class JobRead(BaseModel):
    id: int
    filename: str
    status: str
    price: float
    material: Optional[str] = None
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True

# --- Endpoints ---

@router.post("/upload")
async def upload_stl(file: UploadFile = File(...)):
    if not file.filename.lower().endswith(".stl"):
        raise HTTPException(status_code=400, detail="Only .stl files are allowed")
    
    with NamedTemporaryFile(delete=False, suffix=".stl") as tmp:
        shutil.copyfileobj(file.file, tmp)
        tmp_path = tmp.name

    try:
        your_mesh = mesh.Mesh.from_file(tmp_path)
        volume, _, _ = your_mesh.get_mass_properties()
        os.remove(tmp_path)
        volume_cm3 = volume / 1000.0
        
        return {
            "filename": file.filename, 
            "status": "Uploaded", 
            "volume_cm3": round(volume_cm3, 2),
            "message": "File analyzed successfully"
        }
    except Exception as e:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)
        raise HTTPException(status_code=500, detail=f"Failed to process STL: {str(e)}")

@router.post("/quote", response_model=QuoteResponse)
async def get_quote(request: QuoteRequest, db: Session = Depends(get_db)):
    # 1. Logic: Volume * Density * Cost + Markup
    # TODO: In production, fetch volume from DB/Session instead of hardcoding/trusting client
    volume = 50.0 
    
    density = 1.24
    if "PETG" in request.material.upper():
        density = 1.27
    
    cost_per_g = 0.05
    markup = 5.0
    
    weight = volume * density
    price = (weight * cost_per_g * request.quantity) + markup
    
    # 2. Save Job to DB
    new_job = Job(
        filename=request.filename,
        material=request.material,
        volume_cm3=volume,
        quantity=request.quantity,
        price=round(price, 2),
        status=JobStatus.PENDING
    )
    db.add(new_job)
    db.commit()
    db.refresh(new_job)
    
    return QuoteResponse(
        volume_cm3=volume,
        weight_g=weight,
        total_cost=round(price, 2),
        currency="USD"
    )

@router.get("/jobs", response_model=List[JobRead])
async def list_jobs(db: Session = Depends(get_db)):
    jobs = db.query(Job).order_by(Job.created_at.desc()).all()
    return jobs

@router.post("/jobs/{job_id}/approve")
async def approve_job(job_id: int, db: Session = Depends(get_db)):
    job = db.query(Job).filter(Job.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
        
    job.status = JobStatus.SLICING
    db.commit()
    
    # Trigger Async Slicing Task here
    return {"message": f"Job {job_id} approved. Slicing started..."}

@router.post("/jobs/{job_id}/approve")
async def approve_job(job_id: int):
    # Logic: 
    # 1. Trigger Bambu Slicer CLI
    # 2. Upload .3mf to Printer (FTPS)
    # 3. Send Start Print (MQTT)
    return {"message": f"Job {job_id} approved. Slicing started..."}
