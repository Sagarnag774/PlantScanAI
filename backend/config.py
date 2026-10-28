import os
from pathlib import Path
from typing import List, Set, Tuple


class Settings:
    PROJECT_NAME: str = os.getenv("PLANTSCAN_PROJECT_NAME", "PlantScan AI")
    VERSION: str = "1.0.0"
    API_PREFIX: str = "/api/v1"
    
    # Environment mode: 'development', 'staging', 'production'
    ENVIRONMENT: str = os.getenv("PLANTSCAN_ENV", os.getenv("ENVIRONMENT", "development")).strip().lower()
    DEBUG: bool = os.getenv("PLANTSCAN_DEBUG", "false" if ENVIRONMENT == "production" else "true").strip().lower() in ("true", "1", "yes")
    
    # Thresholds
    CONFIDENCE_THRESHOLD: float = float(os.getenv("PLANTSCAN_CONFIDENCE_THRESHOLD", "0.70"))
    
    # Image constraints & decompression bomb safety
    MAX_IMAGE_SIZE_MB: int = int(os.getenv("PLANTSCAN_MAX_IMAGE_SIZE_MB", "10"))
    MAX_IMAGE_SIZE_BYTES: int = MAX_IMAGE_SIZE_MB * 1024 * 1024
    MAX_IMAGE_PIXELS: int = int(os.getenv("PLANTSCAN_MAX_IMAGE_PIXELS", "10000000"))  # 10 Megapixels max
    MAX_BASE64_PAYLOAD_CHARS: int = int(os.getenv("PLANTSCAN_MAX_BASE64_CHARS", str(15 * 1024 * 1024)))  # ~15MB base64 chars
    MIN_IMAGE_DIMENSIONS: Tuple[int, int] = (32, 32)
    MAX_IMAGE_DIMENSIONS: Tuple[int, int] = (4096, 4096)
    ALLOWED_EXTENSIONS: Set[str] = {".jpg", ".jpeg", ".png", ".webp", ".bmp"}
    ALLOWED_IMAGE_FORMATS: Set[str] = {"JPEG", "PNG", "WEBP", "BMP"}
    ALLOWED_MIME_TYPES: Set[str] = {
        "image/jpeg",
        "image/jpg",
        "image/png",
        "image/webp",
        "image/bmp",
        "application/octet-stream",
    }
    
    # Paths
    PROJECT_ROOT: Path = Path(__file__).resolve().parents[1]
    TREATMENT_DB_DIR: Path = PROJECT_ROOT / "treatment_database"
    TAXONOMY_PATH: Path = PROJECT_ROOT / "datasets" / "reports" / "model" / "final_class_taxonomy_v2.csv"
    WEIGHTS_DIR: Path = PROJECT_ROOT / "ml" / "weights"
    
    # Supported crops list
    SUPPORTED_CROPS: List[str] = [
        "Apple",
        "Banana",
        "Bell pepper",
        "Cotton",
        "Grape",
        "Maize",
        "Mango",
        "Potato",
        "Rice",
        "Tomato",
    ]

    # Model configuration
    DEFAULT_MODEL_NAME: str = "MobileNetV2-PlantScan-v1"
    IMAGE_INPUT_SIZE: Tuple[int, int] = (224, 224)
    # In production, silent fallback to synthetic mock engine must be disabled by default
    ENABLE_MOCK_FALLBACK: bool = (
        os.getenv("PLANTSCAN_ENABLE_MOCK_FALLBACK", "false" if ENVIRONMENT == "production" else "true")
        .strip()
        .lower()
        in ("true", "1", "yes")
    )

    # Security & CORS configuration
    # Simulation headers permit overriding inference results via headers for testing.
    # Must be disabled in production unless explicitly requested.
    ENABLE_SIMULATION_HEADERS: bool = (
        os.getenv("PLANTSCAN_ENABLE_SIMULATION_HEADERS", "false" if ENVIRONMENT == "production" else "true")
        .strip()
        .lower()
        in ("true", "1", "yes")
    )

    # Parse CORS origins from environment (comma-separated), with safe defaults
    _raw_cors = os.getenv("PLANTSCAN_CORS_ORIGINS")
    if _raw_cors:
        CORS_ORIGINS: List[str] = [o.strip() for o in _raw_cors.split(",") if o.strip()]
    elif ENVIRONMENT == "production":
        CORS_ORIGINS: List[str] = ["http://localhost:8000", "http://127.0.0.1:8000"]
    else:
        CORS_ORIGINS: List[str] = ["*"]

    CORS_ALLOW_CREDENTIALS: bool = os.getenv("PLANTSCAN_CORS_ALLOW_CREDENTIALS", "false").strip().lower() in ("true", "1", "yes")

    # Rate limiting & concurrency controls
    RATE_LIMIT_ENABLED: bool = os.getenv("PLANTSCAN_RATE_LIMIT_ENABLED", "true").strip().lower() in ("true", "1", "yes")
    RATE_LIMIT_RPM: int = int(os.getenv("PLANTSCAN_RATE_LIMIT_RPM", "60"))
    MAX_CONCURRENT_INFERENCES: int = int(os.getenv("PLANTSCAN_MAX_CONCURRENT_INFERENCES", "4"))

    # Plant presence validation & non-plant rejection thresholds
    PLANT_VALIDATION_ENABLED: bool = (
        os.getenv("PLANTSCAN_PLANT_VALIDATION_ENABLED", "true").strip().lower() in ("true", "1", "yes")
    )
    PLANT_VALIDATION_THRESHOLD: float = float(os.getenv("PLANTSCAN_PLANT_VALIDATION_THRESHOLD", "0.50"))
    PLANT_AMBIGUOUS_THRESHOLD: float = float(os.getenv("PLANTSCAN_PLANT_AMBIGUOUS_THRESHOLD", "0.35"))
    BLUR_THRESHOLD: float = float(os.getenv("PLANTSCAN_BLUR_THRESHOLD", "20.0"))


settings = Settings()

