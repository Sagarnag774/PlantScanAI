from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from .api.router import api_router
from .config import settings
from .services.inference_engine import get_inference_engine
from .services.treatment_service import get_treatment_service


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Warm up model engine and load treatment database
    print("=" * 60)
    print(f"Starting {settings.PROJECT_NAME} API v{settings.VERSION}")
    print("=" * 60)
    treatment_svc = get_treatment_service()
    engine = get_inference_engine()
    crops = treatment_svc.repository.list_supported_crops()
    print(f"[OK] Inference Engine: {engine.engine_name}")
    print(f"[OK] Treatment Database loaded: {len(crops)} crops, {len(treatment_svc.repository.list_all_canonical_classes())} classes")
    print(f"[OK] Supported crops: {', '.join(crops)}")
    print("=" * 60)
    yield
    print(f"Shutting down {settings.PROJECT_NAME} API...")


app = FastAPI(
    title=f"{settings.PROJECT_NAME} - Backend API",
    version=settings.VERSION,
    description=(
        "Production-ready AI Plant Health Assistant API. "
        "Provides disease classification, plant part detection, out-of-scope/uncertainty rejection, "
        "and Integrated Pest Management (IPM) treatment recommendations."
    ),
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)

# Enable CORS for React Native mobile client, web dashboard, and local testing
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Custom Exception Handler for structured HTTPException details
@app.exception_handler(HTTPException)
async def custom_http_exception_handler(request: Request, exc: HTTPException):
    if isinstance(exc.detail, dict):
        return JSONResponse(status_code=exc.status_code, content=exc.detail)
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "status": "error",
            "error_code": "HTTP_EXCEPTION",
            "message": str(exc.detail),
            "hint": "Check request parameters and try again.",
        },
    )


# Custom Exception Handler for Pydantic Validation Errors
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    errors = exc.errors()
    error_msg = "; ".join([f"{e['loc'][-1]}: {e['msg']}" for e in errors]) if errors else "Validation failed"
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "status": "error",
            "error_code": "VALIDATION_ERROR",
            "message": error_msg,
            "hint": "Check request body/form field formats against the API schema.",
            "details": exc.errors(),
        },
    )


# Root landing endpoint
@app.get("/", tags=["General"])
async def root():
    return {
        "project": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "status": "operational",
        "documentation": "/docs",
        "health_check": "/api/v1/health",
        "predict_endpoint": "/api/v1/predict",
    }


# Mount API routers (both with version prefix /api/v1 and top-level for convenience)
app.include_router(api_router, prefix=settings.API_PREFIX)
app.include_router(api_router)  # Also expose directly (e.g. /predict and /health)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.main:app", host="0.0.0.0", port=8000, reload=True)
