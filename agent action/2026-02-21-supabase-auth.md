# Supabase Auth Integration & Frontend Updates

## Summary
Implemented full-stack authentication using Supabase Auth, secured backend endpoints, and updated the frontend with a seamless login experience and protected admin dashboard.

## Changes

### 1. Backend (FastAPI)
- **Authentication Dependency:** Created `app/api/deps.py` to verify Supabase JWT tokens.
- **Route Protection:**
    - `get_current_user`: Extracts user identity from the `Authorization` header.
    - `get_current_admin`: Restricts access to specific admin emails (configured in `.env`).
- **Endpoints:**
    - Updated `/upload` to associate jobs with the authenticated user's ID (`customer_id`).
    - Protected `/admin` routes (`list_jobs`, `approve_job`) to require admin privileges.
- **Configuration:**
    - Added `ADMIN_EMAIL` to `config.py` and `.env` to control admin access.

### 2. Frontend (React)
- **Supabase Client:** Configured `@supabase/supabase-js` in `src/lib/supabase.ts`.
- **State Management:** Built `AuthContext.tsx` to handle:
    - User session persistence.
    - Login/Logout functions.
    - Admin status verification.
- **UI Components:**
    - Created `AuthModal.tsx`: A responsive modal for Email/Password Sign In and Sign Up.
    - Updated `App.tsx`:
        - Wrapped application in `AuthProvider`.
        - Added Navigation Bar with dynamic User/Sign In buttons.
        - Implemented protected routing for `/admin`.
    - Updated `Home.tsx`:
        - Sends `Authorization: Bearer <token>` header with file uploads if logged in.
    - Updated `Admin.tsx`:
        - Fetches jobs using the auth token.
        - Protects the dashboard from unauthorized access.
        - Improved state management and error handling.
- **Styling:**
    - Fixed Tailwind CSS v4 configuration in `index.css` to ensure theme colors load correctly.

### 3. Bug Fixes
- Resolved module import errors (`Session` type import).
- Fixed `ReferenceError`s in `Home.tsx` and `Admin.tsx` caused by missing imports or state variables.
- Fixed blank screen issues by correcting CSS imports.

## Verification
- Verified user sign-up and sign-in flows.
- Confirmed file uploads are linked to user accounts.
- Verified Admin Dashboard access is restricted to the configured admin email (`eliotbmortimore@gmail.com`).
