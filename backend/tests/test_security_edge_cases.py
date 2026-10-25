import io
from unittest.mock import patch
import pytest
from PIL import Image
from fastapi.testclient import TestClient

from backend.config import settings
from backend.services.image_processor import ImageProcessor, ImageValidationError


def test_security_headers_present(client: TestClient):
    """Verify essential OWASP security headers on responses."""
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    assert response.headers.get("x-content-type-options") == "nosniff"
    assert response.headers.get("x-frame-options") == "SAMEORIGIN"
    assert response.headers.get("x-xss-protection") == "1; mode=block"
    assert response.headers.get("referrer-policy") == "strict-origin-when-cross-origin"


def test_empty_file_upload(client: TestClient):
    """Verify that uploading a 0-byte file returns a clean 400 error."""
    files = {"file": ("empty.jpg", b"", "image/jpeg")}
    response = client.post("/api/v1/predict", files=files)
    assert response.status_code == 400
    data = response.json()
    assert data["status"] == "invalid_image"
    assert data["error_code"] == "EMPTY_FILE"


def test_oversized_file_upload(client: TestClient):
    """Verify that uploading a file exceeding max MB limit returns 400."""
    oversized_bytes = b"0" * (settings.MAX_IMAGE_SIZE_BYTES + 1024)
    files = {"file": ("huge.jpg", oversized_bytes, "image/jpeg")}
    response = client.post("/api/v1/predict", files=files)
    assert response.status_code == 400
    data = response.json()
    assert data["status"] == "invalid_image"
    assert data["error_code"] == "FILE_TOO_LARGE"


def test_unsupported_extension_upload(client: TestClient):
    """Verify that unsupported file extensions are rejected."""
    files = {"file": ("document.pdf", b"%PDF-1.4 dummy content", "application/pdf")}
    response = client.post("/api/v1/predict", files=files)
    assert response.status_code == 400
    data = response.json()
    assert data["status"] == "invalid_image"
    assert data["error_code"] == "UNSUPPORTED_EXTENSION"


def test_disguised_unsupported_image_format():
    """Verify that valid images with disallowed formats (e.g. TIFF) are rejected even with valid extension."""
    img = Image.new("RGB", (64, 64), color=(0, 255, 0))
    buf = io.BytesIO()
    img.save(buf, format="TIFF")
    tiff_bytes = buf.getvalue()

    with pytest.raises(ImageValidationError) as exc_info:
        ImageProcessor.validate_and_load_bytes(tiff_bytes, filename="spoofed.jpg")
    assert exc_info.value.detail["error_code"] == "UNSUPPORTED_IMAGE_FORMAT"


def test_decompression_bomb_rejection():
    """Verify PIL DecompressionBombError is caught and returned safely."""
    with patch("PIL.Image.open") as mock_open:
        mock_img = mock_open.return_value
        mock_img.load.side_effect = Image.DecompressionBombError("Image exceeds safety limits")
        
        with pytest.raises(ImageValidationError) as exc_info:
            ImageProcessor.validate_and_load_bytes(b"dummy_bytes_here", filename="bomb.jpg")
        assert exc_info.value.detail["error_code"] == "DECOMPRESSION_BOMB_DETECTED"


def test_base64_payload_too_large(client: TestClient):
    """Verify that huge Base64 strings are rejected before decoding."""
    huge_str = "A" * (settings.MAX_BASE64_PAYLOAD_CHARS + 50)
    response = client.post("/api/v1/predict/json", json={"image_base64": huge_str})
    assert response.status_code == 400
    data = response.json()
    assert data["status"] == "invalid_image"
    assert data["error_code"] == "BASE64_TOO_LARGE"


def test_base64_invalid_string(client: TestClient):
    """Verify that non-base64 strings return a clean 400."""
    response = client.post("/api/v1/predict/json", json={"image_base64": "!!!NOT_VALID_BASE64!!!"})
    assert response.status_code == 400
    data = response.json()
    assert data["status"] == "invalid_image"


def test_simulation_headers_disabled_in_prod(client: TestClient, valid_leaf_image_bytes):
    """When ENABLE_SIMULATION_HEADERS is False, headers like X-Simulate-Class must be ignored."""
    with patch.object(settings, "ENABLE_SIMULATION_HEADERS", False):
        files = {"file": ("leaf.jpg", valid_leaf_image_bytes, "image/jpeg")}
        headers = {
            "X-Simulate-Class": "banana_cordana",
            "X-Simulate-Confidence": "0.99",
            "X-Simulate-Crop": "Banana",
        }
        response = client.post("/api/v1/predict", files=files, headers=headers)
        assert response.status_code == 200
        data = response.json()
        # Should NOT be forced to Banana Cordana since simulation headers are disabled!
        # With crop_hint=None and tomato leaf, it should be Tomato
        assert data["crop"] != "Banana" or data["disease"]["class_name"] != "banana_cordana"


def test_rate_limiter_exceeded(client: TestClient):
    """Verify rate limiter blocks client exceeding RPM."""
    from backend.services.rate_limiter import rate_limiter
    
    # Save original RPM and set to 3 for testing
    orig_rpm = rate_limiter.requests_per_minute
    try:
        rate_limiter.requests_per_minute = 3
        # Clear existing timestamps
        rate_limiter._requests.clear()
        
        # Make 3 fast calls
        for _ in range(3):
            res = client.post(
                "/api/v1/predict",
                files={"file": ("test.jpg", b"invalid_bytes", "image/jpeg")},
            )
            # Either 400 (bad image) or ok, but not 429
            assert res.status_code != 429

        # 4th call should hit rate limit
        res4 = client.post(
            "/api/v1/predict",
            files={"file": ("test.jpg", b"invalid_bytes", "image/jpeg")},
        )
        assert res4.status_code == 429
        assert res4.json()["error_code"] == "RATE_LIMIT_EXCEEDED"
        assert "Retry-After" in res4.headers
    finally:
        rate_limiter.requests_per_minute = orig_rpm
        rate_limiter._requests.clear()


def test_readiness_probe_degraded_when_mock_in_production(client: TestClient):
    """Verify that in production without weights, readiness returns 503."""
    with patch.object(settings, "ENVIRONMENT", "production"):
        with patch.object(settings, "ENABLE_MOCK_FALLBACK", False):
            with patch("backend.api.health.check_engine_readiness") as mock_check:
                mock_check.return_value = {
                    "ready": False,
                    "engine_name": "MockModelEngine",
                    "is_mock": True,
                    "weights_exist": False,
                    "error": "Real model weights required in production",
                }
                response = client.get("/api/v1/ready")
                assert response.status_code == 503
                data = response.json()
                assert data["status"] == "not_ready"
                assert data["model_ready"] is False

