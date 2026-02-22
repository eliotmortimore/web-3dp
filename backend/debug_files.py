from app.db.database import SessionLocal
from app.db.models import Job
from app.core.config import settings
from supabase import create_client

db = SessionLocal()
supabase = create_client(settings.SUPABASE_URL, settings.SUPABASE_KEY)

jobs = db.query(Job).order_by(Job.id.desc()).limit(10).all()

print(f"{'ID':<5} {'Status':<10} {'Slice':<10} {'Filename':<20} {'File Path':<40} {'Sliced Path':<40}")
print("-" * 130)

for job in jobs:
    print(f"{job.id:<5} {job.status:<10} {job.slice_status:<10} {job.filename:<20} {str(job.filepath):<40} {str(job.sliced_file_path):<40}")
    
    # Check if file exists in Supabase
    if job.filepath:
        try:
            # We can't easily "check exists" without listing or trying to download metadata.
            # verify via public url header check usually easiest or list bucket
            pass
        except Exception as e:
            print(f"  Error checking file: {e}")

print("\n--- Checking Bucket Content (Top level 'jobs' folder) ---")
try:
    # List top level folders in 'jobs'
    # Supabase list returns objects in the path
    res = supabase.storage.from_(settings.SUPABASE_BUCKET).list("jobs")
    for item in res:
        print(f"  {item}")
except Exception as e:
    print(f"Error listing bucket: {e}")
    
db.close()
