import os
import sys
# Add current directory to path so we can import app
sys.path.append(os.getcwd())

from sqlalchemy import create_engine, text
from app.db.database import Base
from app.core.config import settings
# Import models to register them with Base
import app.db.models

def init_db():
    print(f"Connecting to database: {settings.DATABASE_URL.split('@')[1]}") # Print host only for safety
    engine = create_engine(settings.DATABASE_URL)
    
    # 1. Create Tables
    print("Creating tables...")
    Base.metadata.create_all(bind=engine)
    print("Tables created successfully.")
    
    # 2. Setup Storage Bucket via SQL
    print("Setting up Storage Bucket 'web3dp-files'...")
    with engine.connect() as conn:
        try:
            # Create bucket
            # We use text() for raw SQL
            conn.execute(text("""
                INSERT INTO storage.buckets (id, name, public)
                VALUES ('web3dp-files', 'web3dp-files', true)
                ON CONFLICT (id) DO NOTHING;
            """))
            print("Bucket ensured.")

            # We need to enable RLS on objects to make policies work, usually enabled by default but good to check? 
            # Actually storage.objects has RLS enabled by default.
            
            # Helper to create policy if not exists
            # Note: 'CREATE POLICY IF NOT EXISTS' is available in newer Postgres, 
            # but for safety with older versions or specific handling we can wrap in DO block
            
            # Allow public uploads (INSERT)
            # Check if policy exists is hard in simple SQL without a DO block.
            # We'll just try to create and ignore error if it exists.
            
            policies = [
                ("Public Uploads", "INSERT", "WITH CHECK (bucket_id = 'web3dp-files')"),
                ("Public Select", "SELECT", "USING (bucket_id = 'web3dp-files')"),
                ("Public Update", "UPDATE", "USING (bucket_id = 'web3dp-files')"),
                ("Public Delete", "DELETE", "USING (bucket_id = 'web3dp-files')"),
            ]
            
            for name, action, definition in policies:
                try:
                    # Postgres doesn't support CREATE POLICY IF NOT EXISTS until v14+ (Supabase is usually 15+)
                    # But to be safe and simple, we'll try to drop first or just catch error.
                    # Let's use DO block.
                    sql = f"""
                    DO $$
                    BEGIN
                        IF NOT EXISTS (
                            SELECT 1 FROM pg_policies 
                            WHERE tablename = 'objects' 
                            AND policyname = '{name}'
                        ) THEN
                            CREATE POLICY "{name}" ON storage.objects
                            FOR {action} {definition};
                        END IF;
                    END
                    $$;
                    """
                    conn.execute(text(sql))
                    print(f"Policy '{name}' ensured.")
                except Exception as e:
                    print(f"Error setting policy '{name}': {e}")
            
            conn.commit()
            print("Storage policies configured.")
            
        except Exception as e:
            print(f"Error during storage setup: {e}")
            conn.rollback()

if __name__ == "__main__":
    init_db()
