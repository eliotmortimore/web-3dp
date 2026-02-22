from app.core.config import settings
print(f"DB URL: {settings.DATABASE_URL}")

from app.db.database import SessionLocal
from app.db.models import Job

db = SessionLocal()
job = db.query(Job).filter(Job.id == 2).first()
if job:
    print(f"Job {job.id}: Status={job.status}, SliceStatus={job.slice_status}, Vol={job.volume_cm3}")
else:
    print("Job 2 not found")
db.close()
