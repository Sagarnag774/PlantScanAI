from datetime import datetime, timezone
# pyrefly: ignore [missing-import]
from fastapi import APIRouter, Depends, Response, status
from ..config import settings
from ..schemas.common import HealthCheckResponse, InfoResponse, ReadinessResponse
from ..services.inference_engine import (
    BaseModelEngine,
    check_engine_readiness,
    get_inference_engine,
)
from ..services.treatment_service import TreatmentService, get_treatment_service

router = APIRouter(tags=["System & Health"])


@router.get(
    "/health",
    response_model=HealthCheckResponse,
    summary="Liveness / System Health Check",
    description="Check backend API process liveness, active model engine name, and treatment knowledge base status.",
)
async def health_check(
    engine: BaseModelEngine = Depends(get_inference_engine),
    treatment_svc: TreatmentService = Depends(get_treatment_service),
) -> HealthCheckResponse:
    crops = treatment_svc.repository.list_supported_crops()
    return HealthCheckResponse(
        status="healthy",
        service="PlantScan AI API",
        version=settings.VERSION,
        timestamp=datetime.now(timezone.utc).isoformat(),
        active_model_engine=engine.engine_name,
        treatment_database_loaded=len(crops) > 0,
        supported_crops_count=len(crops),
    )


@router.get(
    "/ready",
    response_model=ReadinessResponse,
    summary="Readiness Probe",
    description=(
        "Check whether the service is fully ready to handle inference traffic. "
        "Verifies model tensor allocation, weights availability, and treatment repository readiness. "
        "Returns HTTP 503 if the service cannot safely serve diagnostic requests."
    ),
    responses={
        200: {"description": "Service is ready to handle traffic"},
        503: {"model": ReadinessResponse, "description": "Service is not ready (missing weights, corrupt database)"},
    },
)
async def readiness_check(
    response: Response,
    engine: BaseModelEngine = Depends(get_inference_engine),
    treatment_svc: TreatmentService = Depends(get_treatment_service),
) -> ReadinessResponse:
    engine_readiness = check_engine_readiness()
    crops = treatment_svc.repository.list_supported_crops()
    canonical_classes = treatment_svc.repository.list_all_canonical_classes()

    treatment_ready = len(crops) > 0 and len(canonical_classes) > 0
    model_ready = engine_readiness["ready"]

    is_overall_ready = model_ready and treatment_ready

    if not is_overall_ready:
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
        readiness_status = "not_ready"
    elif engine_readiness.get("is_mock"):
        readiness_status = "degraded" if settings.ENVIRONMENT == "development" else "ready"
    else:
        readiness_status = "ready"

    return ReadinessResponse(
        status=readiness_status,
        service="PlantScan AI API",
        version=settings.VERSION,
        timestamp=datetime.now(timezone.utc).isoformat(),
        model_ready=model_ready,
        model_engine=engine.engine_name,
        treatment_db_ready=treatment_ready,
        supported_crops_count=len(crops),
        classes_count=len(canonical_classes),
        details={
            "environment": settings.ENVIRONMENT,
            "weights_exist": engine_readiness.get("weights_exist", False),
            "is_mock": engine_readiness.get("is_mock", False),
            "error": engine_readiness.get("error"),
        },
    )


@router.get(
    "/info",
    response_model=InfoResponse,
    summary="API & Model Metadata",
    description="Retrieve project information, supported crop species, confidence thresholds, and image upload constraints.",
)
async def api_info(
    treatment_svc: TreatmentService = Depends(get_treatment_service),
) -> InfoResponse:
    return InfoResponse(
        project_name=settings.PROJECT_NAME,
        version=settings.VERSION,
        description="AI-powered plant disease diagnosis and sustainable Integrated Pest Management advisory.",
        supported_crops=treatment_svc.repository.list_supported_crops(),
        confidence_threshold=settings.CONFIDENCE_THRESHOLD,
        max_image_size_mb=settings.MAX_IMAGE_SIZE_MB,
        allowed_formats=sorted(list(settings.ALLOWED_EXTENSIONS)),
    )

