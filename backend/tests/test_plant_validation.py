"""
PlantScanAI - Automated Non-Plant Detection & Rejection Test Suite
Validates all 10 requirements per Section 8 of the specification:
1. Valid plant leaf image (accepted -> returns disease prediction)
2. Person image (rejected -> 422 NON_PLANT_IMAGE)
3. Animal image (rejected -> 422 NON_PLANT_IMAGE)
4. Car image (rejected -> 422 NON_PLANT_IMAGE)
5. Building image (rejected -> 422 NON_PLANT_IMAGE)
6. Landscape without identifiable plant (rejected -> 422 NON_PLANT_IMAGE)
7. Blurry image (rejected -> 422 BLURRY_IMAGE)
8. Corrupted image file (rejected -> 400 CORRUPT_IMAGE / FILE_READ_ERROR)
9. Unsupported file type (rejected -> 400 UNSUPPORTED_EXTENSION)
10. Valid plant with borderline/uncertain validation (rejected -> 422 AMBIGUOUS_IMAGE)
11. Critical Gatekeeper Proof: Disease classifier is NEVER called when an image is rejected!
"""

import io
from unittest.mock import MagicMock, patch
import pytest
from PIL import Image, ImageDraw, ImageFilter
from fastapi.testclient import TestClient

from backend.main import app
from backend.services.inference_engine import get_inference_engine


def _create_jpeg_bytes(img: Image.Image) -> bytes:
    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=95)
    return buf.getvalue()


@pytest.fixture
def test_person_image_bytes() -> bytes:
    img = Image.new("RGB", (224, 224), color=(225, 185, 150))
    d = ImageDraw.Draw(img)
    d.ellipse([(40, 30), (184, 194)], fill=(215, 160, 130))
    d.ellipse([(70, 80), (90, 100)], fill=(20, 20, 20))
    d.ellipse([(134, 80), (154, 100)], fill=(20, 20, 20))
    d.line([(85, 140), (139, 140)], fill=(160, 40, 40), width=3)
    return _create_jpeg_bytes(img)


@pytest.fixture
def test_animal_image_bytes() -> bytes:
    img = Image.new("RGB", (224, 224), color=(150, 100, 55))
    d = ImageDraw.Draw(img)
    d.polygon([(30, 20), (70, 75), (15, 75)], fill=(130, 85, 45))
    d.polygon([(194, 20), (154, 75), (209, 75)], fill=(130, 85, 45))
    d.ellipse([(95, 120), (129, 150)], fill=(10, 10, 10))
    return _create_jpeg_bytes(img)


@pytest.fixture
def test_car_image_bytes() -> bytes:
    img = Image.new("RGB", (224, 224), color=(180, 185, 190))
    d = ImageDraw.Draw(img)
    d.rectangle([(20, 90), (204, 170)], fill=(30, 80, 180))
    d.rectangle([(50, 50), (174, 90)], fill=(200, 225, 245))
    d.ellipse([(35, 150), (75, 190)], fill=(15, 15, 15))
    d.ellipse([(149, 150), (189, 190)], fill=(15, 15, 15))
    for x in range(30, 200, 25):
        d.line([(x, 90), (x, 170)], fill=(10, 10, 10), width=2)
    return _create_jpeg_bytes(img)


@pytest.fixture
def test_building_image_bytes() -> bytes:
    img = Image.new("RGB", (224, 224), color=(160, 160, 165))
    d = ImageDraw.Draw(img)
    d.rectangle([(25, 15), (199, 224)], fill=(150, 70, 50))
    for y in range(30, 210, 35):
        for x in range(40, 185, 35):
            d.rectangle([(x, y), (x + 20, y + 20)], fill=(215, 230, 250))
    return _create_jpeg_bytes(img)


@pytest.fixture
def test_landscape_image_bytes() -> bytes:
    img = Image.new("RGB", (224, 224), color=(110, 180, 255))
    d = ImageDraw.Draw(img)
    d.polygon([(0, 135), (80, 85), (150, 125), (224, 95), (224, 140)], fill=(120, 115, 110))
    d.rectangle([(0, 140), (224, 224)], fill=(65, 65, 70))
    d.line([(112, 150), (112, 224)], fill=(240, 240, 240), width=2)
    return _create_jpeg_bytes(img)


@pytest.fixture
def test_blurry_image_bytes(valid_leaf_image_bytes: bytes) -> bytes:
    with Image.open(io.BytesIO(valid_leaf_image_bytes)) as im:
        blurry = im.filter(ImageFilter.GaussianBlur(radius=20))
        return _create_jpeg_bytes(blurry)


# -------------------------------------------------------------------------
# Test Cases 1 through 10
# -------------------------------------------------------------------------

def test_1_valid_plant_leaf_accepted(client: TestClient, valid_leaf_image_bytes: bytes):
    """Test 1: A valid plant leaf image is accepted and successfully classified."""
    files = {"file": ("leaf.jpg", valid_leaf_image_bytes, "image/jpeg")}
    response = client.post("/api/v1/predict", files=files, data={"crop_hint": "Tomato"})

    assert response.status_code == 200
    data = response.json()
    assert data["status"] in ["success", "uncertain"]
    assert data["crop"] == "Tomato"
    assert "predicted_class" in data
    assert data["predicted_class"] != "unsupported_part_disease"
    assert data["recommendation"] is not None


def test_2_person_image_rejected(client: TestClient, test_person_image_bytes: bytes):
    """Test 2: A photo of a person is rejected with HTTP 422 and NON_PLANT_IMAGE code."""
    files = {"file": ("person.jpg", test_person_image_bytes, "image/jpeg")}
    response = client.post("/api/v1/predict", files=files)

    assert response.status_code == 422
    data = response.json()
    assert data["success"] is False
    assert data["error_code"] == "NON_PLANT_IMAGE"
    assert "does not appear to contain a plant" in data["message"]
    assert data["prediction"] is None


def test_3_animal_image_rejected(client: TestClient, test_animal_image_bytes: bytes):
    """Test 3: An animal photo is rejected with HTTP 422 and NON_PLANT_IMAGE code."""
    files = {"file": ("animal.jpg", test_animal_image_bytes, "image/jpeg")}
    response = client.post("/api/v1/predict", files=files)

    assert response.status_code == 422
    data = response.json()
    assert data["success"] is False
    assert data["error_code"] == "NON_PLANT_IMAGE"
    assert "does not appear to contain a plant" in data["message"]
    assert data["prediction"] is None


def test_4_car_image_rejected(client: TestClient, test_car_image_bytes: bytes):
    """Test 4: A car photo is rejected with HTTP 422 and NON_PLANT_IMAGE code."""
    files = {"file": ("car.jpg", test_car_image_bytes, "image/jpeg")}
    response = client.post("/api/v1/predict", files=files)

    assert response.status_code == 422
    data = response.json()
    assert data["success"] is False
    assert data["error_code"] == "NON_PLANT_IMAGE"
    assert "does not appear to contain a plant" in data["message"]
    assert data["prediction"] is None


def test_5_building_image_rejected(client: TestClient, test_building_image_bytes: bytes):
    """Test 5: An architectural building photo is rejected with HTTP 422 and NON_PLANT_IMAGE code."""
    files = {"file": ("building.jpg", test_building_image_bytes, "image/jpeg")}
    response = client.post("/api/v1/predict", files=files)

    assert response.status_code == 422
    data = response.json()
    assert data["success"] is False
    assert data["error_code"] == "NON_PLANT_IMAGE"
    assert "does not appear to contain a plant" in data["message"]
    assert data["prediction"] is None


def test_6_landscape_without_plant_rejected(client: TestClient, test_landscape_image_bytes: bytes):
    """Test 6: A landscape without identifiable plants is rejected with HTTP 422."""
    files = {"file": ("landscape.jpg", test_landscape_image_bytes, "image/jpeg")}
    response = client.post("/api/v1/predict", files=files)

    assert response.status_code == 422
    data = response.json()
    assert data["success"] is False
    assert data["error_code"] == "NON_PLANT_IMAGE"
    assert "does not appear to contain a plant" in data["message"]
    assert data["prediction"] is None


def test_7_blurry_image_rejected(client: TestClient, test_blurry_image_bytes: bytes):
    """Test 7: A severely blurred image is rejected requesting a clearer photo."""
    files = {"file": ("blurry.jpg", test_blurry_image_bytes, "image/jpeg")}
    response = client.post("/api/v1/predict", files=files)

    assert response.status_code == 422
    data = response.json()
    assert data["success"] is False
    assert data["error_code"] == "BLURRY_IMAGE"
    assert "too blurry" in data["message"].lower()
    assert data["prediction"] is None


def test_8_corrupted_image_rejected(client: TestClient, corrupt_image_bytes: bytes):
    """Test 8: A corrupted image binary is rejected with HTTP 400 without crashing."""
    files = {"file": ("corrupt.jpg", corrupt_image_bytes, "image/jpeg")}
    response = client.post("/api/v1/predict", files=files)

    assert response.status_code == 400
    data = response.json()
    assert data["status"] == "invalid_image"


def test_9_unsupported_file_type_rejected(client: TestClient):
    """Test 9: An unsupported file format (.txt) is rejected with HTTP 400."""
    files = {"file": ("document.txt", b"Hello, this is a text file.", "text/plain")}
    response = client.post("/api/v1/predict", files=files)

    assert response.status_code == 400
    data = response.json()
    assert data["error_code"] == "UNSUPPORTED_EXTENSION"


def test_10_ambiguous_image_requests_clarification(client: TestClient, valid_leaf_image_bytes: bytes):
    """Test 10: A valid plant image that receives an uncertain validation result requests clarification."""
    from ml.plant_validator.validator import ValidationResult

    files = {"file": ("borderline_leaf.jpg", valid_leaf_image_bytes, "image/jpeg")}
    ambig_res = ValidationResult(
        is_valid=False,
        status="ambiguous",
        error_code="AMBIGUOUS_IMAGE",
        message="The presence of a plant or supported plant part cannot be reliably determined. Please upload a closer, clearer photo of the plant leaf or fruit.",
        plant_score=0.42,
    )
    with patch("ml.plant_validator.validator.PlantImageValidator.validate", return_value=ambig_res):
        response = client.post("/api/v1/predict", files=files)

    assert response.status_code == 422
    data = response.json()
    assert data["success"] is False
    assert data["error_code"] == "AMBIGUOUS_IMAGE"
    assert data["prediction"] is None


def test_11_classifier_is_never_called_on_rejected_image(client: TestClient, test_car_image_bytes: bytes):
    """
    Test 11 (CRITICAL GATEKEEPER):
    Verifies that the disease classifier engine.predict is NEVER called when an image is rejected.
    """
    engine = get_inference_engine()
    with patch.object(engine, "predict", wraps=engine.predict) as mock_predict:
        files = {"file": ("car.jpg", test_car_image_bytes, "image/jpeg")}
        response = client.post("/api/v1/predict", files=files)

        assert response.status_code == 422
        # Assert disease classifier was NEVER invoked!
        assert mock_predict.call_count == 0, "Disease classifier must NEVER be called on a non-plant image!"


def test_12_base64_non_plant_rejection(client: TestClient, test_car_image_bytes: bytes):
    """Test 12: Base64 JSON endpoint also enforces plant validation and rejects non-plant images."""
    import base64
    b64_str = f"data:image/jpeg;base64,{base64.b64encode(test_car_image_bytes).decode('utf-8')}"
    payload = {"image_base64": b64_str, "crop_hint": "Tomato"}

    response = client.post("/api/v1/predict/json", json=payload)

    assert response.status_code == 422
    data = response.json()
    assert data["success"] is False
    assert data["error_code"] == "NON_PLANT_IMAGE"
    assert data["prediction"] is None
