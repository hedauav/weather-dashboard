import sys
from pathlib import Path
from fastapi import Request

# Add backend directory to Python path
backend_dir = Path(__file__).resolve().parent.parent / "backend"
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from app.main import app

@app.middleware("http")
async def restore_original_path(request: Request, call_next):
    """
    When Vercel rewrites /api/v1/... to /api/index, it sets the
    x-matched-path header to the original URL (e.g. /api/v1/health).
    We restore that so FastAPI's router can match the correct route.
    """
    # x-matched-path contains the original incoming request path before rewriting
    original_path = (
        request.headers.get("x-matched-path")
        or request.headers.get("x-vercel-matched-path")
    )
    if original_path:
        request.scope["path"] = original_path
        # Also update root_path if needed
        request.scope["root_path"] = ""

    return await call_next(request)
