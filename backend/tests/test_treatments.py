from fastapi.testclient import TestClient
from treatment_database.repository import TreatmentRepository


CANONICAL_TOMATO_CLASSES = [
    "tomato_early_blight",
    "tomato_late_blight",
    "tomato_bacterial_spot",
    "tomato_septoria_leaf_spot",
    "tomato_leaf_mold",
    "tomato_spider_mites",
    "tomato_target_spot",
    "tomato_yellow_leaf_curl_virus",
    "tomato_mosaic_virus",
    "tomato_healthy",
]


def test_all_10_tomato_classes_exist():
    repo = TreatmentRepository()
    for cls_name in CANONICAL_TOMATO_CLASSES:
        record = repo.get_by_class(cls_name)
        assert record is not None, f"Missing treatment record for {cls_name}"
        assert record["crop"] == "Tomato"
        assert len(record.get("organic_measures", [])) >= 1, f"Missing organic measures for {cls_name}"
        assert len(record.get("prevention_measures", [])) >= 1, f"Missing prevention measures for {cls_name}"
        assert len(record.get("sources", [])) >= 1, f"Missing literature/extension sources for {cls_name}"


def test_healthy_classes_no_chemical_pesticides():
    repo = TreatmentRepository()
    healthy_classes = ["tomato_healthy", "potato_healthy", "banana_healthy", "cotton_healthy", "mango_healthy", "healthy_rice_leaf"]
    for h_cls in healthy_classes:
        record = repo.get_by_class(h_cls)
        if record:
            chemicals = record.get("chemical_measures", [])
            assert len(chemicals) == 0, f"Healthy class {h_cls} must not recommend chemical pesticides"


def test_chemical_safety_attributes():
    repo = TreatmentRepository()
    record = repo.get_by_class("tomato_early_blight")
    assert record is not None
    chemicals = record.get("chemical_measures", [])
    assert len(chemicals) >= 1
    for chem in chemicals:
        assert "safety_precautions" in chem
        assert "dosage" in chem
        assert chem.get("caution_level") in ["Low", "Moderate", "High"]


def test_disclaimers_present():
    repo = TreatmentRepository()
    disclaimers = repo.disclaimers
    assert "general_disclaimer" in disclaimers
    assert "chemical_safety_warning" in disclaimers
    assert len(disclaimers["general_disclaimer"]) > 20


def test_list_crops_endpoint(client: TestClient):
    response = client.get("/api/v1/treatments/crops")
    assert response.status_code == 200
    crops = response.json()
    assert isinstance(crops, list)
    assert "Tomato" in crops
    assert "Rice" in crops
    assert "Potato" in crops


def test_list_classes_endpoint(client: TestClient):
    response = client.get("/api/v1/treatments/classes")
    assert response.status_code == 200
    classes = response.json()
    assert isinstance(classes, list)
    assert "tomato_early_blight" in classes
    assert "tomato_late_blight" in classes


def test_get_treatment_endpoint_valid(client: TestClient):
    response = client.get("/api/v1/treatments/Tomato/tomato_early_blight")
    assert response.status_code == 200
    data = response.json()
    assert "Tomato Early Blight" in data["summary"]
    assert len(data["organic"]) >= 1
    assert len(data["chemical"]) >= 1
    assert len(data["prevention"]) >= 1
    assert len(data["disclaimer"]) > 0


def test_get_treatment_endpoint_not_found(client: TestClient):
    response = client.get("/api/v1/treatments/Tomato/alien_disease_xyz")
    assert response.status_code == 404
    data = response.json()
    assert data["status"] == "error"
    assert data["error_code"] == "TREATMENT_NOT_FOUND"
