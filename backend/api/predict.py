import logging
import time
from typing import Optional
# pyrefly: ignore [missing-import]
from fastapi import (
    APIRouter,
    Depends,
    File,
    Form,
    Header,
    HTTPException,
    Request,
    UploadFile,
    status,
)
from starlette.concurrency import run_in_threadpool

from ..config import settings
from ..schemas.common import ErrorDetail, PredictionStatus
from ..schemas.prediction import Base64PredictRequest, PredictionResponse
from ..services.image_processor import ImageProcessor, ImageValidationError, PlantValidationError
from ..services.inference_engine import BaseModelEngine, get_inference_engine
from ..services.rate_limiter import get_inference_semaphore, rate_limiter
from ..services.treatment_service import TreatmentService, get_treatment_service
from ml.plant_validator.validator import PlantImageValidator

logger = logging.getLogger("plantscan.api.predict")

router = APIRouter(tags=["Disease Prediction"])


@router.post(
    "/predict",
    response_model=PredictionResponse,
    summary="Diagnose Plant Disease from Image Upload",
    description=(
        "Upload a plant leaf/crop image (JPEG, PNG, WebP) to classify disease, identify plant part, "
        "calculate Plant Health Score, and obtain sustainable Integrated Pest Management (IPM) recommendations."
    ),
    responses={
        400: {"model": ErrorDetail, "description": "Invalid image format, corrupted file, or bad dimensions"},
        422: {"model": ErrorDetail, "description": "Non-plant or ambiguous image rejected by validation stage"},
        429: {"model": ErrorDetail, "description": "Rate limit exceeded"},
        500: {"model": ErrorDetail, "description": "Internal server or inference failure"},
    },
)
async def predict_image(
    http_request: Request,
    file: UploadFile = File(..., description="Plant image file (JPEG, PNG, WebP, max 10MB)"),
    crop_hint: Optional[str] = Form(None, description="Optional target crop hint (e.g., 'Tomato', 'Rice', 'Mango')"),
    plant_part_hint: Optional[str] = Form(None, description="Optional plant part hint ('Leaf', 'Stem', 'Fruit', 'Bark')"),
    language: Optional[str] = Form("en", description="Preferred response language code ('en', 'kn', 'hi')"),
    x_simulate_class: Optional[str] = Header(None, alias="X-Simulate-Class", description="Test override: forced class"),
    x_simulate_confidence: Optional[float] = Header(None, alias="X-Simulate-Confidence", description="Test override: forced confidence"),
    x_simulate_crop: Optional[str] = Header(None, alias="X-Simulate-Crop", description="Test override: forced crop"),
    x_simulate_status: Optional[str] = Header(None, alias="X-Simulate-Status", description="Test override: forced status"),
    engine: BaseModelEngine = Depends(get_inference_engine),
    treatment_svc: TreatmentService = Depends(get_treatment_service),
) -> PredictionResponse:
    # 1. Enforce rate limiting
    await rate_limiter.check(http_request)

    start_time = time.perf_counter()

    # 2. Validate and load image
    try:
        image_bytes = await file.read()
        pil_image = await run_in_threadpool(
            ImageProcessor.validate_and_load_bytes, image_bytes, filename=file.filename
        )
    except ImageValidationError:
        raise
    except Exception as e:
        logger.warning("File upload read error: %s", e)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "status": "invalid_image",
                "error_code": "FILE_READ_ERROR",
                "message": "Could not process uploaded file: The image data is corrupted or invalid.",
                "hint": "Ensure the uploaded file is an uncorrupted JPEG, PNG, or WebP image.",
            },
        )

    # 2.5. Stage 0: Plant-Image Validation (Strict Gatekeeper)
    # Rejects non-plant images (cars, people, buildings, animals, landscapes) and blurry photos BEFORE disease classification.
    if settings.PLANT_VALIDATION_ENABLED:
        validation_res = await run_in_threadpool(
            PlantImageValidator.validate,
            image=pil_image,
            plant_part_hint=plant_part_hint,
            crop_hint=crop_hint,
            blur_threshold=settings.BLUR_THRESHOLD,
            min_plant_score=settings.PLANT_VALIDATION_THRESHOLD,
            ambiguous_threshold=settings.PLANT_AMBIGUOUS_THRESHOLD,
        )
        if not validation_res.is_valid:
            logger.info("Plant validation rejected upload: %s (%s)", validation_res.error_code, validation_res.status)
            raise PlantValidationError(
                message=validation_res.message,
                error_code=validation_res.error_code,
                hint="Please upload a clear image of a plant leaf or another supported plant part.",
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                details=validation_res.details,
            )

    input_array = await run_in_threadpool(ImageProcessor.preprocess_for_model, pil_image)

    # 3. Simulation header check (only permitted when ENABLE_SIMULATION_HEADERS is True)
    force_sim = None
    if settings.ENABLE_SIMULATION_HEADERS:
        if x_simulate_class or x_simulate_confidence is not None or x_simulate_crop:
            force_sim = {
                "class": x_simulate_class or "tomato_early_blight",
                "confidence": x_simulate_confidence if x_simulate_confidence is not None else 0.94,
                "crop": x_simulate_crop or "Tomato",
            }

    # 4. Concurrency-guarded inference execution
    try:
        async with get_inference_semaphore():
            prediction = await run_in_threadpool(
                engine.predict,
                image_array=input_array,
                crop_hint=crop_hint,
                plant_part_hint=plant_part_hint,
                force_simulation=force_sim,
                original_image=pil_image,
            )
    except Exception as e:
        logger.error("AI model inference failure: %s", e, exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "status": "error",
                "error_code": "INFERENCE_FAILED",
                "message": "AI model inference failed. Please try again later.",
                "hint": "Please try again later or contact system administration.",
            },
        )

    inference_time_ms = round((time.perf_counter() - start_time) * 1000, 2)
    forced_st = (
        PredictionStatus(x_simulate_status)
        if (settings.ENABLE_SIMULATION_HEADERS and x_simulate_status)
        else None
    )

    try:
        response = await run_in_threadpool(
            treatment_svc.build_prediction_response,
            prediction=prediction,
            inference_time_ms=inference_time_ms,
            forced_status=forced_st,
            language=language,
        )
    except Exception as e:
        logger.error("Treatment response building failure: %s", e, exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "status": "error",
                "error_code": "TREATMENT_LOOKUP_FAILED",
                "message": "Failed to compile treatment recommendations.",
                "hint": "Please try again later or consult an agricultural extension specialist.",
            },
        )

    return response


@router.post(
    "/predict/json",
    response_model=PredictionResponse,
    summary="Diagnose Plant Disease from Base64 Image JSON",
    description="Send a Base64-encoded image in a JSON payload for environments where multipart uploads are inconvenient.",
    responses={
        400: {"model": ErrorDetail, "description": "Invalid Base64 string or invalid image"},
        422: {"model": ErrorDetail, "description": "Non-plant or ambiguous image rejected by validation stage"},
        429: {"model": ErrorDetail, "description": "Rate limit exceeded"},
        500: {"model": ErrorDetail, "description": "Internal server or inference failure"},
    },
)
async def predict_base64_json(
    http_request: Request,
    request: Base64PredictRequest,
    engine: BaseModelEngine = Depends(get_inference_engine),
    treatment_svc: TreatmentService = Depends(get_treatment_service),
) -> PredictionResponse:
    # 1. Enforce rate limiting
    await rate_limiter.check(http_request)

    start_time = time.perf_counter()

    # 2. Validate and decode Base64
    try:
        pil_image = await run_in_threadpool(ImageProcessor.load_from_base64, request.image_base64)
    except ImageValidationError:
        raise
    except Exception as e:
        logger.warning("Base64 image load error: %s", e)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "status": "invalid_image",
                "error_code": "BASE64_DECODE_ERROR",
                "message": "Could not decode Base64 image payload.",
                "hint": "Verify Base64 encoding and image format.",
            },
        )

    # 2.5. Stage 0: Plant-Image Validation (Strict Gatekeeper)
    if settings.PLANT_VALIDATION_ENABLED:
        validation_res = await run_in_threadpool(
            PlantImageValidator.validate,
            image=pil_image,
            plant_part_hint=request.plant_part_hint,
            crop_hint=request.crop_hint,
            blur_threshold=settings.BLUR_THRESHOLD,
            min_plant_score=settings.PLANT_VALIDATION_THRESHOLD,
            ambiguous_threshold=settings.PLANT_AMBIGUOUS_THRESHOLD,
        )
        if not validation_res.is_valid:
            logger.info("Plant validation rejected base64 upload: %s (%s)", validation_res.error_code, validation_res.status)
            raise PlantValidationError(
                message=validation_res.message,
                error_code=validation_res.error_code,
                hint="Please upload a clear image of a plant leaf or another supported plant part.",
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                details=validation_res.details,
            )

    input_array = await run_in_threadpool(ImageProcessor.preprocess_for_model, pil_image)

    # 3. Concurrency-guarded inference execution
    try:
        async with get_inference_semaphore():
            prediction = await run_in_threadpool(
                engine.predict,
                image_array=input_array,
                crop_hint=request.crop_hint,
                plant_part_hint=request.plant_part_hint,
                original_image=pil_image,
            )
    except Exception as e:
        logger.error("AI model inference failure (base64): %s", e, exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "status": "error",
                "error_code": "INFERENCE_FAILED",
                "message": "AI model inference failed. Please try again later.",
                "hint": "Please try again later or contact system administration.",
            },
        )

    inference_time_ms = round((time.perf_counter() - start_time) * 1000, 2)

    try:
        return await run_in_threadpool(
            treatment_svc.build_prediction_response,
            prediction=prediction,
            inference_time_ms=inference_time_ms,
            language=request.language,
        )
    except Exception as e:
        logger.error("Treatment response building failure (base64): %s", e, exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "status": "error",
                "error_code": "TREATMENT_LOOKUP_FAILED",
                "message": "Failed to compile treatment recommendations.",
                "hint": "Please try again later or consult an agricultural extension specialist.",
            },
        )

