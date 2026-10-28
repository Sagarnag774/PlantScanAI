import base64
import io
import logging
from pathlib import Path
from typing import Any, Dict, Optional, Tuple
import numpy as np
from PIL import Image, ImageOps, UnidentifiedImageError
from fastapi import HTTPException, status

from ..config import settings

logger = logging.getLogger("plantscan.image_processor")

# Configure PIL decompression bomb ceiling to protect against malicious zip-bombs / massive pixel maps
Image.MAX_IMAGE_PIXELS = settings.MAX_IMAGE_PIXELS


class ImageValidationError(HTTPException):
    def __init__(
        self,
        message: str,
        hint: Optional[str] = None,
        error_code: str = "INVALID_IMAGE",
        status_code: int = status.HTTP_400_BAD_REQUEST,
    ):
        super().__init__(
            status_code=status_code,
            detail={
                "status": "invalid_image",
                "error_code": error_code,
                "message": message,
                "hint": hint or "Please upload a valid JPEG, PNG, or WebP image under 10MB.",
            },
        )


class PlantValidationError(HTTPException):
    """
    Raised when an uploaded image fails the Stage 0 plant presence validation
    (e.g., non-plant images such as cars, people, animals, buildings, or blurry/ambiguous images).
    Returns HTTP 422 Unprocessable Entity with structured failure details.
    """

    def __init__(
        self,
        message: str,
        error_code: str = "NON_PLANT_IMAGE",
        hint: Optional[str] = None,
        status_code: int = getattr(status, "HTTP_422_UNPROCESSABLE_CONTENT", 422),
        details: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(
            status_code=status_code,
            detail={
                "success": False,
                "status": "invalid_image",
                "error_code": error_code,
                "message": message,
                "hint": hint or "Please upload a clear image of a plant leaf or another supported plant part.",
                "prediction": None,
                "details": details or {},
            },
        )


class ImageProcessor:
    """
    Validates, sanitizes, and prepares raw image bytes or base64 strings
    for machine learning inference.
    """

    @staticmethod
    def validate_and_load_bytes(image_bytes: bytes, filename: Optional[str] = None) -> Image.Image:
        if not image_bytes:
            raise ImageValidationError(
                message="Uploaded file is empty (0 bytes).",
                hint="Please select a valid image file from your device.",
                error_code="EMPTY_FILE",
            )

        if len(image_bytes) > settings.MAX_IMAGE_SIZE_BYTES:
            raise ImageValidationError(
                message=f"Image file size ({len(image_bytes) / (1024*1024):.1f} MB) exceeds maximum allowed {settings.MAX_IMAGE_SIZE_MB} MB.",
                hint=f"Compress or resize the image to under {settings.MAX_IMAGE_SIZE_MB} MB before uploading.",
                error_code="FILE_TOO_LARGE",
            )

        if filename:
            ext = Path(filename).suffix.lower()
            if ext and ext not in settings.ALLOWED_EXTENSIONS:
                raise ImageValidationError(
                    message=f"Unsupported file format '{ext}'. Allowed formats: {', '.join(sorted(settings.ALLOWED_EXTENSIONS))}.",
                    hint="Convert your image to JPEG or PNG before uploading.",
                    error_code="UNSUPPORTED_EXTENSION",
                )

        try:
            image = Image.open(io.BytesIO(image_bytes))
            image.load()
        except Image.DecompressionBombError:
            logger.warning("Rejected upload due to PIL DecompressionBombError")
            raise ImageValidationError(
                message="Image pixel dimensions exceed maximum allowed safety limit (decompression bomb protection).",
                hint="Please downscale your photo before uploading.",
                error_code="DECOMPRESSION_BOMB_DETECTED",
            )
        except UnidentifiedImageError:
            raise ImageValidationError(
                message="The uploaded file is not a recognized image or is severely corrupted.",
                hint="Ensure you are uploading a valid JPEG, PNG, BMP, or WebP image.",
                error_code="UNIDENTIFIED_IMAGE",
            )
        except Exception as e:
            logger.error("Image loading failure: %s", e)
            raise ImageValidationError(
                message="Failed to process image: The image file appears corrupted or unreadable.",
                hint="The image file appears corrupted or truncated. Please take a new photo.",
                error_code="CORRUPT_IMAGE",
            )

        # Inspect real decoded format (preventing extension spoofing)
        if image.format and image.format.upper() not in settings.ALLOWED_IMAGE_FORMATS:
            raise ImageValidationError(
                message=f"Disguised or unsupported image format '{image.format}'. Allowed formats: {', '.join(sorted(settings.ALLOWED_IMAGE_FORMATS))}.",
                hint="Please provide a standard JPEG, PNG, or WebP image.",
                error_code="UNSUPPORTED_IMAGE_FORMAT",
            )

        width, height = image.size
        min_w, min_h = settings.MIN_IMAGE_DIMENSIONS
        max_w, max_h = settings.MAX_IMAGE_DIMENSIONS

        if width < min_w or height < min_h:
            raise ImageValidationError(
                message=f"Image dimensions ({width}x{height}) are too small. Minimum required is {min_w}x{min_h} pixels.",
                hint="Upload a higher resolution photo for accurate plant disease detection.",
                error_code="IMAGE_TOO_SMALL",
            )

        if width > max_w or height > max_h:
            raise ImageValidationError(
                message=f"Image dimensions ({width}x{height}) exceed maximum allowed {max_w}x{max_h} pixels.",
                hint="Downscale or crop the photo before sending.",
                error_code="IMAGE_TOO_LARGE",
            )

        try:
            image = ImageOps.exif_transpose(image)
        except Exception:
            pass

        if image.mode != "RGB":
            image = image.convert("RGB")

        return image

    @classmethod
    def load_from_base64(cls, base64_str: str) -> Image.Image:
        if not base64_str or not base64_str.strip():
            raise ImageValidationError(
                message="Base64 image string is empty.",
                hint="Provide a valid Base64 encoded image string.",
                error_code="EMPTY_BASE64",
            )

        if len(base64_str) > settings.MAX_BASE64_PAYLOAD_CHARS:
            raise ImageValidationError(
                message=f"Base64 image payload length ({len(base64_str)} chars) exceeds maximum allowed limit ({settings.MAX_BASE64_PAYLOAD_CHARS} chars).",
                hint=f"Reduce image size to under {settings.MAX_IMAGE_SIZE_MB} MB before encoding.",
                error_code="BASE64_TOO_LARGE",
            )

        clean_str = base64_str.strip()
        if "," in clean_str and ("data:image" in clean_str or "base64" in clean_str):
            clean_str = clean_str.split(",", 1)[1]

        try:
            image_bytes = base64.b64decode(clean_str, validate=True)
        except Exception as e:
            logger.warning("Base64 decoding failed: %s", e)
            raise ImageValidationError(
                message="Failed to decode Base64 string: Invalid Base64 data.",
                hint="Verify that your Base64 string is correctly formatted without invalid characters.",
                error_code="INVALID_BASE64",
            )

        return cls.validate_and_load_bytes(image_bytes)

    @staticmethod
    def preprocess_for_model(
        image: Image.Image,
        target_size: Tuple[int, int] = settings.IMAGE_INPUT_SIZE,
    ) -> np.ndarray:
        resized = image.resize(target_size, Image.Resampling.BILINEAR)
        arr = np.array(resized, dtype=np.float32)
        return np.expand_dims(arr, axis=0)

