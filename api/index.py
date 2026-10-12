import sys
from pathlib import Path
from fastapi import Request

# Add backend directory to Python path
backend_dir = Path(__file__).resolve().parent.parent / "backend"
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from app.main import app

@app.middleware("http")
async def strip_path_prefix(request: Request, call_next):
    # If Vercel rewrites to /api/index.py, strip it so FastAPI router matches cleanly
    path = request.scope.get("path", "")
    for prefix in ("/api/index.py", "/api/index"):
        if path.startswith(prefix):
            remainder = path[len(prefix):]
            if not remainder.startswith("/"):
                remainder = "/" + remainder
            request.scope["path"] = remainder
            break
    return await call_next(request)
