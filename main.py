"""
Render entrypoint shim.
Render may start either `uvicorn main:app` (root) or `uvicorn backend.main:app`.
Both must serve the NEW backend (backend/main.py), never the legacy monolith.
"""
try:
    from backend.main import app  # type: ignore
except Exception:
    # Fallback for local runs where repo root is already on sys.path differently
    from backend.main import app  # type: ignore

if __name__ == "__main__":
    import os
    import uvicorn
    uvicorn.run("backend.main:app", host="0.0.0.0", port=int(os.getenv("PORT", "8000")))
