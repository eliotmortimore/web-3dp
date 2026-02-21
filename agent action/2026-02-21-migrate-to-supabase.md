# Migrate to Supabase: PostgreSQL + Storage

## Summary
Migrated the backend infrastructure from local SQLite and filesystem storage to Supabase (PostgreSQL + Object Storage). This enables cloud persistence, scalability, and easier deployment.

## Changes

### 1. Database Migration (SQLite -> PostgreSQL)
- **Dependencies:** Added `psycopg2-binary` to `requirements.txt`.
- **Configuration:** Updated `app/core/config.py` to read `DATABASE_URL` from environment variables.
- **Connection:** Switched SQLAlchemy engine to use PostgreSQL driver.
- **Schema:** 
    - Tables (`jobs`, `materials`) are now created in Supabase PostgreSQL.
    - Added `customer_id` and `order_id` columns to `Job` table for future features.

### 2. File Storage Migration (Local -> Supabase Storage)
- **Dependencies:** Added `supabase` Python client.
- **Configuration:** Added `SUPABASE_URL`, `SUPABASE_KEY`, and `SUPABASE_BUCKET` settings.
- **Uploads:**
    - Updated `/upload` endpoint to stream files directly to Supabase bucket `web3dp-files`.
    - Files are stored as `jobs/{job_id}/{filename}`.
- **Processing:**
    - Updated background slicing task to download source files from Supabase.
    - Sliced G-code/3MF files are uploaded back to Supabase.
    - Metadata parsing now fetches the file temporarily from storage.

### 3. Infrastructure
- **Environment:** Created `.env` file for managing secrets (excluded from git).
- **Initialization:** Created `init_supabase.py` script to:
    - Create database tables.
    - Create storage bucket `web3dp-files`.
    - Configure public access policies for the storage bucket.

## Verification
- Validated database connection using IPv4-compatible connection pooler.
- Verified table creation and storage bucket configuration.
- Confirmed backend server starts successfully and connects to remote services.
