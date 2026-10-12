import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

from app.config import settings
from app.database import db_manager
from app.routes.analysis_routes import router as analysis_router

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("climate_app")

# Rate limiter setup
limiter = Limiter(key_func=get_remote_address, default_limits=[settings.RATE_LIMIT_DEFAULT])

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Initializing Climate Hazard Trend Analyzer Backend...")
    await db_manager.connect()
    yield
    await db_manager.close()
    logger.info("Shutdown complete.")

app = FastAPI(
    title=settings.PROJECT_NAME,
    version="1.0.0",
    description="ERA5-based Climate Hazard Trend Analyzer for Dygnify Ventures Case Study",
    lifespan=lifespan
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# CORS configuration
origins = [origin.strip() for origin in settings.ALLOWED_ORIGINS.split(",")]
if "*" in origins:
    origins = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global safe error handling
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled error processing {request.url.path}: {str(exc)}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": "An internal server error occurred. Please verify your inputs or retry shortly."}
    )

# Health endpoint (PRD 8.1)
@app.get(f"{settings.API_V1_PREFIX}/health", tags=["Health"])
async def health_check():
    return {
        "status": "healthy",
        "service": settings.PROJECT_NAME,
        "dataset": settings.DATASET_NAME,
        "database_connected": db_manager.is_connected,
        "algorithm_version": settings.ALGORITHM_VERSION,
        "imputation_policy": settings.IMPUTATION_POLICY_VERSION
    }

# Register API routes
app.include_router(analysis_router, prefix=settings.API_V1_PREFIX, tags=["Analysis"])

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
