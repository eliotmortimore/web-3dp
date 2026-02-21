from typing import Generator, Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from supabase import create_client, Client
from app.core.config import settings

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token", auto_error=False)

# Initialize Supabase Client
supabase: Client = create_client(settings.SUPABASE_URL, settings.SUPABASE_KEY)

def get_current_user_id(token: Optional[str] = Depends(oauth2_scheme)) -> Optional[str]:
    """
    Returns the user ID (UUID) if a valid JWT is provided.
    Returns None if no token or invalid token.
    DOES NOT raise an exception (for optional auth).
    """
    if not token:
        return None
    
    try:
        user = supabase.auth.get_user(token)
        return user.user.id
    except Exception:
        return None

def get_current_user(token: str = Depends(oauth2_scheme)) -> dict:
    """
    Returns the full user object if authenticated.
    Raises 401 if not authenticated.
    """
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )
    try:
        user_response = supabase.auth.get_user(token)
        return user_response.user
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

def get_current_admin(user = Depends(get_current_user)):
    """
    Dependency to check if the current user is an admin.
    """
    if not user.email or user.email != "admin@web3dp.com": # Using hardcoded email or env var
         # Better to use env var
         admin_email = getattr(settings, "ADMIN_EMAIL", "admin@web3dp.com")
         if user.email != admin_email:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not enough permissions"
            )
    return user
