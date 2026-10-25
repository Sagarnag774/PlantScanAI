from fastapi.testclient import TestClient


def test_root_endpoint(client: TestClient):
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["project"] == "PlantScan AI"
    assert "version" in data
    assert data["status"] == "operational"


def test_health_check_endpoint(client: TestClient):
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["service"] == "PlantScan AI API"
    assert data["treatment_database_loaded"] is True
    assert data["supported_crops_count"] == 10
    assert "active_model_engine" in data


def test_info_endpoint(client: TestClient):
    response = client.get("/api/v1/info")
    assert response.status_code == 200
    data = response.json()
    assert data["project_name"] == "PlantScan AI"
    assert data["confidence_threshold"] == 0.70
    assert "Tomato" in data["supported_crops"]
    assert "Mango" in data["supported_crops"]
    assert "Apple" in data["supported_crops"]
    assert data["max_image_size_mb"] == 10
    assert ".jpg" in data["allowed_formats"]


def test_readiness_probe_endpoint(client: TestClient):
    response = client.get("/api/v1/ready")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] in ("ready", "degraded")
    assert data["service"] == "PlantScan AI API"
    assert data["model_ready"] is True
    assert data["treatment_db_ready"] is True
    assert data["supported_crops_count"] == 10
    assert data["classes_count"] == 46
    assert "details" in data

