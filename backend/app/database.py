from fastapi import HTTPException
from supabase import create_client, Client
from .config import SUPABASE_URL, SUPABASE_KEY

_supabase: Client | None = None

def get_supabase() -> Client:
    global _supabase
    if _supabase is not None:
        return _supabase
    if not SUPABASE_URL or not SUPABASE_KEY:
        raise HTTPException(500, "Server misconfigured: SUPABASE_URL / SUPABASE_KEY missing")
    try:
        _supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
    except Exception as e:
        raise HTTPException(500, f"Failed to init Supabase: {e}")
    return _supabase

# Proxy for legacy imports: from .database import supabase
class _Proxy:
    def __getattr__(self, name):
        return getattr(get_supabase(), name)

supabase = _Proxy()  # type: ignore
