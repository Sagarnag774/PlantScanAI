from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class PredictionStatus(str, Enum):
    SUCCESS = "success"
    UNCERTAIN = "uncertain"
    UNKNOWN = "unknown"
    INVALID_IMAGE = "invalid_image"
    UNSUPPORTED_CROP = "unsupported_crop"
    ERROR = "error"


class HealthCheckResponse(BaseModel):
    status: str = Field(..., description="System health status ('healthy', 'degraded')")
    service: str = Field(default="PlantScan AI API")
    version: str = Field(..., description="API Version")
    timestamp: str = Field(..., description="ISO 8601 timestamp")
    active_model_engine: str = Field(..., description="Active AI model engine in memory")
    treatment_database_loaded: bool = Field(..., description="Status of treatment DB loading")
    supported_crops_count: int = Field(..., description="Total crops with treatment data")


class InfoResponse(BaseModel):
    project_name: str
    version: str
    description: str
    supported_crops: List[str]
    confidence_threshold: float
    max_image_size_mb: int
    allowed_formats: List[str]


class ErrorDetail(BaseModel):
    status: PredictionStatus = Field(default=PredictionStatus.ERROR)
    error_code: str = Field(..., description="Machine-readable error code")
    message: str = Field(..., description="Human-readable explanation of error")
    hint: Optional[str] = Field(None, description="Suggested action to resolve the issue")
    details: Optional[Dict[str, Any]] = None


class ReadinessResponse(BaseModel):
    status: str = Field(..., description="Readiness status ('ready', 'not_ready', 'degraded')")
    service: str = Field(default="PlantScan AI API")
    version: str = Field(..., description="API Version")
    timestamp: str = Field(..., description="ISO 8601 timestamp")
    model_ready: bool = Field(..., description="True if inference engine is ready to serve predictions")
    model_engine: str = Field(..., description="Name of the active inference engine")
    treatment_db_ready: bool = Field(..., description="True if treatment database is loaded")
    supported_crops_count: int = Field(..., description="Total crops with treatment data")
    classes_count: int = Field(..., description="Total canonical classes configured")
    details: Optional[Dict[str, Any]] = None

