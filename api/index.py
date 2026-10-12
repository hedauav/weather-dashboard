import sys
from pathlib import Path
from fastapi import Request
import logging

logger = logging.getLogger("uvicorn.error")

# Add backend directory to Python path
backend_dir = Path(__file__).resolve().parent.parent / "backend"
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from app.main import app

@app.middleware("http")
async def log_and_strip_path_prefix(request: Request, call_next):
    raw_path = request.scope.get("path", "")
    logger.info(f"[Vercel Function] Incoming raw scope path: {raw_path}")
    
    # In Vercel rewrites, destination /api/index.py passes either:
    # 1. /api/index.py
    # 2. /api/index.py/api/v1/...
    # 3. or when rewritten directly: /api/v1/...
    for prefix in ("/api/index.py", "/api/index"):
        if raw_path == prefix:
            # The rewrite replaced the path with just the script name!
            # Recover the original requested path from headers or query if present:
            orig = request.headers.get("x-matched-path") or request.headers.get("x-vercel-matched-path")
            if orig:
                logger.info(f"[Vercel Function] Recovered original path from header: {orig}")
                request.scope["path"] = orig
            break
        elif raw_path.startswith(prefix):
            remainder = raw_path[len(prefix):]
            if not remainder.startswith("/"):
                remainder = "/" + remainder
            logger.info(f"[Vercel Function] Stripped prefix '{prefix}', new path: {remainder}")
            request.scope["path"] = remainder
            break

    response = await call_next(request)
    logger.info(f"[Vercel Function] Response status for {request.scope.get('path')}: {response.status_code}")
    return response
