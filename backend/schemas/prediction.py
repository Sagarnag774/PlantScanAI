from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field
from .common import PredictionStatus


class TreatmentItem(BaseModel):
    name: str = Field(..., description="Name or title of the treatment / remedy")
    method: Optional[str] = Field(None, description="Detailed instruction on how to prepare and apply")
    application: Optional[str] = Field(None, description="Application method (e.g. foliar spray, root drench)")
    frequency: Optional[str] = Field(None, description="Recommended repetition interval")
    active_ingredient: Optional[str] = Field(None, description="Chemical active ingredient if applicable")
    dosage: Optional[str] = Field(None, description="Recommended safe dosage dilution")
    safety_precautions: Optional[str] = Field(None, description="PPE and safety precautions")
    caution_level: Optional[str] = Field(None, description="Toxicity / caution category (None, Low, Moderate, High)")


class RecommendationResponse(BaseModel):
    summary: str = Field(..., description="High-level advisory summary")
    organic: List[TreatmentItem] = Field(default_factory=list, description="Priority 1: Organic & biological solutions")
    chemical: List[TreatmentItem] = Field(default_factory=list, description="Priority 2: Chemical interventions (if severe/approved)")
    prevention: List[str] = Field(default_factory=list, description="Priority 3: Cultural & preventive agricultural practices")
    safety_notes: List[str] = Field(default_factory=list, description="Safety and environmental warnings")
    photo_guidance: Optional[List[str]] = Field(None, description="Tips for taking clearer diagnostic photos")
    disclaimer: str = Field(..., description="Responsible agricultural advisory disclaimer")
    sources: List[str] = Field(default_factory=list, description="Literature and extension reference sources")


class PredictionResponse(BaseModel):
    status: PredictionStatus = Field(..., description="Prediction status (success, uncertain, unknown, etc.)")
    crop: str = Field(..., description="Detected or targeted crop name (e.g., 'Tomato', 'Unknown')")
    predicted_class: str = Field(..., description="Canonical disease/healthy class identifier")
    display_name: str = Field(..., description="Human-readable title (e.g., 'Tomato Early Blight')")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Model prediction confidence score [0.0 - 1.0]")
    is_healthy: bool = Field(default=False, description="Flag indicating if the crop is healthy")
    plant_part: Optional[str] = Field(default="Leaf", description="Plant part identified (Leaf, Fruit, Stem, Bark)")
    plant_health_score: int = Field(..., ge=0, le=100, description="Estimated Plant Health Score (0 - 100)")
    recommendation: Optional[RecommendationResponse] = Field(None, description="Structured care and treatment advice")
    model_version: str = Field(default="MobileNetV2-PlantScan-v1", description="Identifier of the model used")
    inference_time_ms: float = Field(default=0.0, description="Inference latency in milliseconds")
    message: Optional[str] = Field(None, description="Contextual message or diagnosis notes")


class Base64PredictRequest(BaseModel):
    image_base64: str = Field(..., description="Base64-encoded image string (with or without data:image/jpeg;base64, prefix)")
    crop_hint: Optional[str] = Field(None, description="Optional crop hint to guide classification")
    plant_part_hint: Optional[str] = Field(None, description="Optional plant part hint (Leaf, Stem, Fruit, Bark)")
    language: Optional[str] = Field("en", description="Preferred language code for response (e.g. 'en', 'kn', 'hi')")
