import io
from fastapi.testclient import TestClient


def test_predict_valid_image(client: TestClient, valid_leaf_image_bytes: bytes):
    files = {"file": ("leaf.jpg", valid_leaf_image_bytes, "image/jpeg")}
    response = client.post("/api/v1/predict", files=files)
    
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert data["crop"] == "Tomato"
    assert "predicted_class" in data
    assert data["confidence"] >= 0.70
    assert 0 <= data["plant_health_score"] <= 100
    assert data["recommendation"] is not None
    assert len(data["recommendation"]["disclaimer"]) > 0
    assert len(data["recommendation"]["organic"]) >= 1
    assert len(data["recommendation"]["prevention"]) >= 1


def test_predict_forced_simulation_healthy(client: TestClient, valid_leaf_image_bytes: bytes):
    files = {"file": ("tomato_healthy.jpg", valid_leaf_image_bytes, "image/jpeg")}
    headers = {
        "X-Simulate-Class": "tomato_healthy",
        "X-Simulate-Confidence": "0.96",
        "X-Simulate-Crop": "Tomato",
    }
    response = client.post("/api/v1/predict", files=files, headers=headers)
    
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert data["predicted_class"] == "tomato_healthy"
    assert data["is_healthy"] is True
    assert data["confidence"] == 0.96
    assert data["plant_health_score"] >= 90
    assert len(data["recommendation"]["chemical"]) == 0  # No chemicals for healthy plants
    assert len(data["recommendation"]["organic"]) >= 1


def test_predict_uncertain_low_confidence(client: TestClient, valid_leaf_image_bytes: bytes):
    files = {"file": ("ambiguous.jpg", valid_leaf_image_bytes, "image/jpeg")}
    headers = {
        "X-Simulate-Class": "tomato_early_blight",
        "X-Simulate-Confidence": "0.45",
        "X-Simulate-Crop": "Tomato",
    }
    response = client.post("/api/v1/predict", files=files, headers=headers)
    
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "uncertain"
    assert data["confidence"] == 0.45
    assert len(data["recommendation"]["chemical"]) == 0  # No chemicals for uncertain detections
    assert data["recommendation"]["photo_guidance"] is not None
    assert len(data["recommendation"]["photo_guidance"]) >= 2
    assert "below" in data["recommendation"]["summary"].lower()


def test_predict_unsupported_crop(client: TestClient, valid_leaf_image_bytes: bytes):
    files = {"file": ("dragonfruit.jpg", valid_leaf_image_bytes, "image/jpeg")}
    data_form = {"crop_hint": "DragonFruit"}
    response = client.post("/api/v1/predict", files=files, data=data_form)
    
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "unsupported_crop"
    assert data["predicted_class"] == "unsupported_crop"
    assert "outside the current diagnostic scope" in data["message"]


def test_predict_invalid_corrupt_image(client: TestClient, corrupt_image_bytes: bytes):
    files = {"file": ("corrupt.jpg", corrupt_image_bytes, "image/jpeg")}
    response = client.post("/api/v1/predict", files=files)
    
    assert response.status_code == 400
    data = response.json()
    assert data["status"] == "invalid_image"
    assert data["error_code"] == "INVALID_IMAGE"
    assert "corrupted" in data["message"].lower() or "not a recognized image" in data["message"].lower()


def test_predict_invalid_extension(client: TestClient):
    files = {"file": ("document.txt", b"This is plain text, not an image.", "text/plain")}
    response = client.post("/api/v1/predict", files=files)
    
    assert response.status_code == 400
    data = response.json()
    assert data["status"] == "invalid_image"
    assert "Unsupported file format" in data["message"]


def test_predict_tiny_dimensions(client: TestClient, tiny_image_bytes: bytes):
    files = {"file": ("tiny.jpg", tiny_image_bytes, "image/jpeg")}
    response = client.post("/api/v1/predict", files=files)
    
    assert response.status_code == 400
    data = response.json()
    assert data["status"] == "invalid_image"
    assert "too small" in data["message"].lower()


def test_predict_empty_file(client: TestClient):
    files = {"file": ("empty.jpg", b"", "image/jpeg")}
    response = client.post("/api/v1/predict", files=files)
    
    assert response.status_code == 400
    data = response.json()
    assert data["status"] == "invalid_image"
    assert "empty" in data["message"].lower()


def test_predict_json_base64_valid(client: TestClient, valid_base64_image: str):
    payload = {
        "image_base64": valid_base64_image,
        "crop_hint": "Tomato",
        "language": "en",
    }
    response = client.post("/api/v1/predict/json", json=payload)
    
    assert response.status_code == 200
    data = response.json()
    assert data["status"] in ["success", "uncertain"]
    assert data["crop"] == "Tomato"
    assert "predicted_class" in data


def test_predict_json_base64_invalid(client: TestClient):
    payload = {
        "image_base64": "NOT_VALID_BASE64_GARBAGE!!!",
    }
    response = client.post("/api/v1/predict/json", json=payload)
    
    assert response.status_code == 400
    data = response.json()
    assert data["status"] == "invalid_image"
