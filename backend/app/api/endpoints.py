from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
from fastapi import APIRouter, File, UploadFile, HTTPException, Depends, BackgroundTasks
import shutil
import os
from tempfile import NamedTemporaryFile
from stl import mesh

from sqlalchemy.orm import Session
from app.db.database import get_db
from app.db.models import Job, Material, JobStatus
from app.services.slicer import BambuSlicer
from app.services.bambu_client import BambuPrinter
from app.services.metadata import parse_3mf_metadata
import trimesh

from app.core.config import settings
from app.api import deps
from supabase import create_client, Client

router = APIRouter()
supabase: Client = create_client(settings.SUPABASE_URL, settings.SUPABASE_KEY)
slicer = BambuSlicer()
printer = BambuPrinter()

# --- Background Task ---
def analyze_and_slice_job(job_id: int, db: Session):
    """
    1. Download from Supabase
    2. Analyze Mesh (Volume)
    3. Run Slicer (Weight, Time, Gcode)
    4. Upload Result to Supabase
    5. Update Job in DB
    """
    from app.db.database import SessionLocal
    bg_db = SessionLocal()
    
    try:
        job = bg_db.query(Job).filter(Job.id == job_id).first()
        if not job:
            return

        print(f"[Task] Starting analysis for Job {job_id}...")
        job.slice_status = "ANALYZING"
        bg_db.commit()

        # Step 1: Download File
        if not job.filepath:
            job.slice_status = "FAILED"
            bg_db.commit()
            return

        local_input_path = os.path.join(UPLOAD_DIR, f"temp_{job.id}_{job.filename}")
        try:
            res = supabase.storage.from_(settings.SUPABASE_BUCKET).download(job.filepath)
            with open(local_input_path, "wb") as f:
                f.write(res)
        except Exception as e:
            print(f"[Task] Download error: {e}")
            job.slice_status = "FAILED"
            bg_db.commit()
            return

        # Step 2: Geometry Analysis
        try:
            # Try numpy-stl first
            try:
                your_mesh = mesh.Mesh.from_file(local_input_path)
                raw_vol, _, _ = your_mesh.get_mass_properties()
                job.volume_cm3 = float(raw_vol) / 1000.0
            except:
                # Fallback to trimesh
                mesh_obj = trimesh.load(local_input_path)
                if hasattr(mesh_obj, 'volume'):
                    job.volume_cm3 = mesh_obj.volume / 1000.0
                elif hasattr(mesh_obj, 'convex_hull'):
                    job.volume_cm3 = mesh_obj.convex_hull.volume / 1000.0
        except Exception as e:
            print(f"[Task] Vol calc error: {e}")
            job.volume_cm3 = 50.0 # Fallback

        # Step 3: Slicing
        output_filename = f"job_{job.id}.gcode.3mf"
        output_path = os.path.join(UPLOAD_DIR, output_filename)
        
        # Call Slicer Service
        result = slicer.slice_and_parse(local_input_path, output_path)
        
        if result["success"]:
            # Upload Sliced File to Supabase
            sliced_storage_path = f"jobs/{job.id}/{output_filename}"
            try:
                with open(output_path, "rb") as f:
                    supabase.storage.from_(settings.SUPABASE_BUCKET).upload(sliced_storage_path, f)
                
                job.filament_weight_g = result["weight_g"]
                job.print_time_seconds = result["print_time_s"]
                job.sliced_file_path = sliced_storage_path
                job.slice_status = "COMPLETED"
                
                # Calculate Price
                cost_per_g = 0.05
                markup = 5.0
                machine_rate_per_sec = 3.0 / 3600.0
                
                material_cost = job.filament_weight_g * cost_per_g
                machine_cost = job.print_time_seconds * machine_rate_per_sec
                total_price = material_cost + machine_cost + markup
                job.price = round(total_price * job.quantity, 2)
                
            except Exception as e:
                print(f"[Task] Upload sliced file error: {e}")
                job.slice_status = "FAILED"
            
        else:
            job.slice_status = "FAILED"
            print(f"[Task] Slicing failed.")

        bg_db.commit()
        print(f"[Task] Job {job_id} analysis complete. Price: ${job.price}")
        
        # Cleanup
        if os.path.exists(local_input_path):
            os.remove(local_input_path)
        if os.path.exists(output_path):
            os.remove(output_path)

    except Exception as e:
        print(f"[Task] Critical Error: {e}")
    finally:
        bg_db.close()

# --- Pydantic Schemas (DTOs) ---
class QuoteRequest(BaseModel):
    filename: str
    material: str
    quantity: int

class QuoteResponse(BaseModel):
    job_id: int
    status: str
    volume_cm3: Optional[float] = None
    weight_g: Optional[float] = None
    print_time: Optional[str] = None
    price: Optional[float] = None
    currency: str = "USD"

class JobRead(BaseModel):
    id: int
    filename: str
    status: str
    slice_status: Optional[str] = "PENDING"
    price: float
    quantity: int
    material: Optional[str] = None
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class JobDetailResponse(JobRead):
    volume_cm3: Optional[float] = None
    weight_g: Optional[float] = None
    print_time_seconds: Optional[int] = None
    sliced_file_path: Optional[str] = None
    file_url: Optional[str] = None
    sliced_file_url: Optional[str] = None
    metadata: Optional[dict] = None

# --- Endpoints ---

UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

@router.post("/upload", response_model=QuoteResponse)
async def upload_stl(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    material: str = "PLA",
    quantity: int = 1,
    db: Session = Depends(get_db),
    user_id: Optional[str] = Depends(deps.get_current_user_id)
):
    if not file.filename.lower().endswith(".stl"):
        raise HTTPException(status_code=400, detail="Only .stl files are allowed")
    
    # 1. Create Job Immediately (PENDING)
    new_job = Job(
        filename=file.filename,
        material=material,
        quantity=quantity,
        status=JobStatus.PENDING,
        slice_status="PENDING",
        volume_cm3=0.0,
        price=0.0,
        customer_id=user_id # Save User ID if logged in
    )
    db.add(new_job)
    db.commit()
    db.refresh(new_job)
    
    # 2. Upload to Supabase
    try:
        file_content = await file.read()
        storage_path = f"jobs/{new_job.id}/{file.filename}"
        supabase.storage.from_(settings.SUPABASE_BUCKET).upload(storage_path, file_content)
        
        new_job.filepath = storage_path
        db.commit()
    except Exception as e:
        print(f"Upload failed: {e}")
        db.delete(new_job)
        db.commit()
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")
    
    # 3. Trigger Background Analysis
    background_tasks.add_task(analyze_and_slice_job, new_job.id, db)
    
    return QuoteResponse(
        job_id=new_job.id,
        status="ANALYZING"
    )

@router.get("/jobs/{job_id}/status", response_model=QuoteResponse)
async def check_job_status(job_id: int, db: Session = Depends(get_db)):
    job = db.query(Job).filter(Job.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
        
    return QuoteResponse(
        job_id=job.id,
        status=job.slice_status,
        volume_cm3=job.volume_cm3,
        weight_g=job.filament_weight_g,
        price=job.price,
        print_time=f"{job.print_time_seconds // 60}m" if job.print_time_seconds else None,
        currency="USD"
    )

@router.get("/jobs/{job_id}/details", response_model=JobDetailResponse)
async def get_job_details(job_id: int, db: Session = Depends(get_db)):
    job = db.query(Job).filter(Job.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    # Generate Public URLs
    file_url = None
    sliced_file_url = None
    
    if job.filepath:
        # Assuming public bucket for now. If private, use create_signed_url
        file_url = supabase.storage.from_(settings.SUPABASE_BUCKET).get_public_url(job.filepath)
        
    if job.sliced_file_path:
        sliced_file_url = supabase.storage.from_(settings.SUPABASE_BUCKET).get_public_url(job.sliced_file_path)

    # Parse metadata from the sliced 3MF file if it exists
    metadata = {}
    if job.sliced_file_path:
        try:
             temp_path = os.path.join(UPLOAD_DIR, f"meta_{job.id}.3mf")
             res = supabase.storage.from_(settings.SUPABASE_BUCKET).download(job.sliced_file_path)
             with open(temp_path, "wb") as f:
                 f.write(res)
             metadata = parse_3mf_metadata(temp_path)
             if os.path.exists(temp_path):
                 os.remove(temp_path)
        except Exception as e:
             print(f"Metadata fetch error: {e}")
        
    return JobDetailResponse(
        id=job.id,
        filename=job.filename,
        status=job.status,
        slice_status=job.slice_status,
        price=job.price,
        quantity=job.quantity,
        material=job.material,
        created_at=job.created_at,
        volume_cm3=job.volume_cm3,
        weight_g=job.filament_weight_g,
        print_time_seconds=job.print_time_seconds,
        sliced_file_path=job.sliced_file_path,
        file_url=file_url,
        sliced_file_url=sliced_file_url,
        metadata=metadata
    )

@router.post("/quote")
async def legacy_quote():
    return {"message": "Deprecated. Use /upload directly."}

@router.get("/jobs", response_model=List[JobRead])
async def list_jobs(db: Session = Depends(get_db), current_user = Depends(deps.get_current_admin)):
    jobs = db.query(Job).order_by(Job.created_at.desc()).all()
    return jobs

@router.post("/jobs/{job_id}/approve")
async def approve_job(job_id: int, db: Session = Depends(get_db), current_user = Depends(deps.get_current_admin)):
    job = db.query(Job).filter(Job.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    if job.slice_status != "COMPLETED":
         raise HTTPException(status_code=400, detail="Job slicing not complete yet.")

    if not job.sliced_file_path:
         raise HTTPException(status_code=500, detail="Sliced file path missing.")

    # 1. Download Sliced File
    temp_path = os.path.join(UPLOAD_DIR, f"print_{job.id}.3mf")
    try:
        res = supabase.storage.from_(settings.SUPABASE_BUCKET).download(job.sliced_file_path)
        with open(temp_path, "wb") as f:
            f.write(res)
    except Exception as e:
         raise HTTPException(status_code=500, detail=f"Failed to download sliced file: {e}")

    # 2. Upload to Printer
    printer_filename = f"job_{job.id}.gcode.3mf"
    upload_success = printer.upload_file(temp_path, printer_filename)
    
    # Cleanup temp file
    if os.path.exists(temp_path):
        os.remove(temp_path)

    if not upload_success:
        job.status = JobStatus.FAILED
        db.commit()
        raise HTTPException(status_code=500, detail="Failed to upload to printer")

    # 3. Start Print
    print_success = printer.send_print_command(printer_filename)
    if not print_success:
         job.status = JobStatus.FAILED
         db.commit()
         raise HTTPException(status_code=500, detail="Failed to start print command")
    
    job.status = JobStatus.PRINTING
    db.commit()
    
    return {"message": f"Job {job_id} sent to printer successfully."}
