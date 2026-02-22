from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime, timezone
from fastapi import APIRouter, File, UploadFile, HTTPException, Depends, BackgroundTasks
import shutil
import os
import time
from tempfile import NamedTemporaryFile

from sqlalchemy.orm import Session
from app.db.database import get_db
from app.db.models import Job, Material, JobStatus
from app.services.slicer import BambuSlicer
from app.services.bambu_client import BambuPrinter
from app.services.metadata import parse_3mf_metadata
from app.services.estimation import EstimationService
import trimesh

from app.core.config import settings
from app.api import deps
from app.api.deps import supabase

router = APIRouter()
slicer = BambuSlicer()
printer = BambuPrinter()
estimator = EstimationService()

UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

# --- Background Task ---
def perform_admin_slicing(job_id: int):
    """
    Background task for Admin-triggered slicing using Bambu Studio.
    """
    from app.db.database import SessionLocal
    bg_db = SessionLocal()
    
    try:
        job = bg_db.query(Job).filter(Job.id == job_id).first()
        if not job:
            return

        print(f"[Admin Task] Starting slicing for Job {job_id}...")
        job.slice_status = "SLICING"
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
            print(f"[Admin Task] Download error: {e}")
            job.slice_status = "FAILED"
            bg_db.commit()
            return

        # Step 2: Run Real Slicer
        output_filename = f"job_{job.id}.gcode.3mf"
        output_path = os.path.join(UPLOAD_DIR, output_filename)
        
        result = slicer.slice_file(local_input_path, output_path)
        
        if result["success"]:
            # Upload Sliced File to Supabase
            sliced_storage_path = f"jobs/{job.id}/{output_filename}"
            try:
                with open(output_path, "rb") as f:
                    supabase.storage.from_(settings.SUPABASE_BUCKET).upload(
                        sliced_storage_path, 
                        f,
                        {"content-type": "application/vnd.ms-package.3dmanufacturing-3dmodel+xml", "upsert": "true"}
                    )
                
                job.sliced_file_path = sliced_storage_path
                job.slice_status = "COMPLETED"
                
                # Optional: Update weight/time if real metadata is available
                # (We might want to keep the estimated price or update it? For now, keep estimated)
                
            except Exception as e:
                print(f"[Admin Task] Upload sliced file error: {e}")
                job.slice_status = "FAILED"
            
        else:
            job.slice_status = "FAILED"
            print(f"[Admin Task] Slicing failed: {result.get('error')}")

        bg_db.commit()
        print(f"[Admin Task] Job {job_id} slicing complete.")
        
        # Cleanup
        if os.path.exists(local_input_path):
            os.remove(local_input_path)
        if os.path.exists(output_path):
            os.remove(output_path)

    except Exception as e:
        print(f"[Admin Task] Critical Error: {e}")
    finally:
        bg_db.close()

from app.services.pricing import pricing_service

# --- Pydantic Schemas (DTOs) ---
class QuoteRequest(BaseModel):
    filename: str
    material: str
    quantity: int

class UpdateJobRequest(BaseModel):
    quantity: Optional[int] = None
    material: Optional[str] = None
    color: Optional[str] = None
    status: Optional[str] = None

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

@router.patch("/jobs/{job_id}", response_model=JobRead)
async def update_job(
    job_id: int, 
    request: UpdateJobRequest,
    db: Session = Depends(get_db),
    user_id: Optional[str] = Depends(deps.get_current_user_id)
):
    job = db.query(Job).filter(Job.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
        
    # Security check: require authentication and ownership
    if not user_id:
        raise HTTPException(status_code=401, detail="Authentication required")
    if job.customer_id and job.customer_id != user_id:
        raise HTTPException(status_code=403, detail="Not authorized")

    # Update fields
    if request.quantity is not None:
        job.quantity = request.quantity
    if request.material is not None:
        job.material = request.material
    if request.color is not None:
        job.color = request.color
    if request.status is not None:
        job.status = request.status

    # Recalculate Price if quantity/material changed
    if request.quantity is not None or request.material is not None:
        vol = job.volume_cm3 or 0.0
        time_s = job.print_time_seconds or 0
        mat = job.material
        qty = job.quantity
        
        quote = pricing_service.calculate_price(
            volume_cm3=vol,
            material=mat,
            estimated_time_s=time_s,
            quantity=qty
        )
        job.price = quote["total_price"]
        
        # Re-calc unit weight based on density
        density = pricing_service.FILAMENTS.get(mat.upper(), {}).get("density", 1.24)
        job.filament_weight_g = vol * density

    db.commit()
    db.refresh(job)
    return job

@router.post("/upload", response_model=QuoteResponse)
async def upload_stl(
    file: UploadFile = File(...),
    material: str = "PLA",
    quantity: int = 1,
    db: Session = Depends(get_db),
    user_id: Optional[str] = Depends(deps.get_current_user_id)
):
    if not file.filename.lower().endswith(".stl"):
        raise HTTPException(status_code=400, detail="Only .stl files are allowed")
    
    # 1. Save locally temporarily for estimation
    temp_path = os.path.join(UPLOAD_DIR, f"estimate_{file.filename}")
    try:
        with open(temp_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
            
        # 2. Synchronous Estimation
        estimation = estimator.analyze_stl(temp_path, material)
        if not estimation["success"]:
             raise HTTPException(status_code=400, detail=f"Analysis failed: {estimation.get('error')}")
        
        # Calculate Price using Service
        est_vol = estimation["volume_cm3"]
        est_time = estimation["estimated_print_time_s"]
        
        quote = pricing_service.calculate_price(
            volume_cm3=est_vol,
            material=material,
            estimated_time_s=est_time,
            quantity=quantity
        )
        
        total_price = quote["total_price"]
        est_weight = estimation["estimated_weight_g"] # Unit weight from estimation
        
        # 3. Create Job (PENDING_ADMIN_REVIEW)
        new_job = Job(
            filename=file.filename,
            material=material,
            quantity=quantity,
            status=JobStatus.PENDING,
            slice_status="PENDING", # Needs admin review
            volume_cm3=est_vol,
            filament_weight_g=est_weight,
            print_time_seconds=est_time,
            price=total_price,
            customer_id=user_id 
        )
        db.add(new_job)
        db.commit()
        db.refresh(new_job)
        
        # 4. Upload to Supabase (Async or Sync? Sync is safer here)
        # Reset file pointer to read again
        file.file.seek(0) 
        file_content = file.file.read()
        
        storage_path = f"jobs/{new_job.id}/{file.filename}"
        
        # Try to delete existing file first to avoid 409 Conflict
        try:
            print(f"Checking for existing file at {storage_path}...")
            # We list the folder to check existence (folder is jobs/{id})
            folder_path = f"jobs/{new_job.id}"
            existing_files = supabase.storage.from_(settings.SUPABASE_BUCKET).list(folder_path)
            
            # Check if file exists in the list
            if existing_files and any(f.get('name') == file.filename for f in existing_files):
                print(f"File exists. Deleting {storage_path}...")
                supabase.storage.from_(settings.SUPABASE_BUCKET).remove([storage_path])
                time.sleep(0.5)
        except Exception as remove_err:
            print(f"Pre-check/Remove failed (ignoring): {remove_err}")

        # Upload with upsert
        try:
            supabase.storage.from_(settings.SUPABASE_BUCKET).upload(
                storage_path, 
                file_content, 
                {"content-type": "model/stl", "upsert": "true"}
            )
        except Exception as upload_err:
            # Fallback: if upload failed, try one last delete and retry
            print(f"Upload failed: {upload_err}. Retrying with forced delete...")
            try:
                supabase.storage.from_(settings.SUPABASE_BUCKET).remove([storage_path])
                time.sleep(1.0)
                supabase.storage.from_(settings.SUPABASE_BUCKET).upload(
                    storage_path, 
                    file_content, 
                    {"content-type": "model/stl", "upsert": "true"}
                )
            except Exception as retry_err:
                raise Exception(f"Final upload retry failed: {retry_err}")
        
        new_job.filepath = storage_path
        db.commit()
        
    except HTTPException as he:
        raise he
    except Exception as e:
        print(f"Upload/Estimate failed: {e}")
        if 'new_job' in locals():
            db.delete(new_job)
            db.commit()
        raise HTTPException(status_code=500, detail=f"Processing failed: {str(e)}")
    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)
    
    return QuoteResponse(
        job_id=new_job.id,
        status="ESTIMATED",
        volume_cm3=new_job.volume_cm3,
        weight_g=new_job.filament_weight_g,
        price=new_job.price,
        print_time=f"{new_job.print_time_seconds // 60}m",
        currency="USD"
    )

@router.post("/jobs/{job_id}/slice")
async def trigger_admin_slice(
    job_id: int, 
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user = Depends(deps.get_current_admin)
):
    """
    Admin-only endpoint to trigger real slicing.
    """
    job = db.query(Job).filter(Job.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
        
    background_tasks.add_task(perform_admin_slicing, job.id)
    
    return {"message": "Slicing started in background", "job_id": job.id}

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

@router.get("/jobs", response_model=List[JobRead])
async def list_jobs(db: Session = Depends(get_db), current_user = Depends(deps.get_current_admin)):
    jobs = db.query(Job).order_by(Job.created_at.desc()).all()
    return jobs

@router.post("/jobs/{job_id}/approve")
async def approve_job(job_id: int, db: Session = Depends(get_db), current_user = Depends(deps.get_current_admin)):
    """
    Triggers the printer to start printing the already sliced file.
    """
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

    # 2. Upload to Printer (FTPS)
    # Ensure remote filename is unique and ends with .gcode.3mf
    printer_filename = f"job_{job.id}_{int(datetime.now(timezone.utc).timestamp())}.gcode.3mf"
    
    # We use a background task logic here usually, but for "approve" synchronous might be better feedback?
    # Let's keep it sync for now as upload takes < 10s usually
    upload_success = printer.upload_file(temp_path, printer_filename)
    
    # Cleanup temp file
    if os.path.exists(temp_path):
        os.remove(temp_path)

    if not upload_success:
        # Don't fail the job, just the request
        raise HTTPException(status_code=500, detail="Failed to upload file to printer. Check printer connection.")

    # 3. Start Print (MQTT)
    # TODO: Pass project specific settings if needed (bed type, etc)
    print_success = printer.send_print_command(printer_filename, project_id=str(job.id))
    
    if not print_success:
         raise HTTPException(status_code=500, detail="Failed to send start command to printer.")
    
    job.status = JobStatus.PRINTING
    db.commit()
    
    return {"message": f"Job {job_id} sent to printer successfully.", "printer_file": printer_filename}
