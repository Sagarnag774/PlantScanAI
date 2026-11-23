"""
Verification Script for PlantScanAI Section 12 Requirements:
Case A: Non-plant image (Photo of a car)
Case B: Valid plant image (Clear tomato leaf)
Case C: Ambiguous image (Very blurry image)
Case D: Corrupted image (Invalid file bytes)
"""
import io
import os
import sys

# Ensure project root is in sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import numpy as np
import cv2
from PIL import Image
from fastapi.testclient import TestClient

from backend.main import app
from ml.plant_validator.validator import PlantImageValidator

client = TestClient(app)

def create_car_image_bytes():
    # Synthetic metallic silver/blue car with black windshield and wheels
    img = np.ones((300, 400, 3), dtype=np.uint8) * 180  # asphalt gray
    # Car body: metallic blue rectangle
    cv2.rectangle(img, (50, 140), (350, 230), (140, 80, 40), -1)
    # Windshield / cabin
    pts = np.array([[100, 140], [140, 80], [280, 80], [310, 140]], np.int32)
    cv2.fillPoly(img, [pts], (40, 40, 40))
    # Wheels
    cv2.circle(img, (110, 230), 30, (20, 20, 20), -1)
    cv2.circle(img, (290, 230), 30, (20, 20, 20), -1)
    # Chrome hubcaps
    cv2.circle(img, (110, 230), 12, (220, 220, 220), -1)
    cv2.circle(img, (290, 230), 12, (220, 220, 220), -1)

    pil_img = Image.fromarray(cv2.cvtColor(img, cv2.COLOR_BGR2RGB))
    buf = io.BytesIO()
    pil_img.save(buf, format="JPEG", quality=90)
    return buf.getvalue()

def get_real_tomato_leaf_bytes():
    import glob
    candidates = glob.glob("datasets/PlantVillage/**/Tomato*/**/*.JPG", recursive=True) + \
                 glob.glob("datasets/PlantVillage/**/Tomato*/**/*.jpg", recursive=True)
    if candidates:
        with open(candidates[0], "rb") as f:
            return f.read(), candidates[0]
    # Fallback to rich synthetic leaf
    img = np.ones((256, 256, 3), dtype=np.uint8) * 230
    cv2.ellipse(img, (128, 128), (80, 45), 30, 0, 360, (40, 140, 35), -1)
    pil_img = Image.fromarray(cv2.cvtColor(img, cv2.COLOR_BGR2RGB))
    buf = io.BytesIO()
    pil_img.save(buf, format="JPEG")
    return buf.getvalue(), "synthetic"

def create_blurry_image_bytes():
    # High-contrast shapes that are heavily out-of-focus (Laplacian variance < 20, but std_dev > 15)
    img = np.ones((256, 256, 3), dtype=np.uint8) * 230
    cv2.circle(img, (80, 80), 50, (30, 140, 30), -1)
    cv2.circle(img, (170, 170), 60, (20, 100, 20), -1)
    blurred = cv2.GaussianBlur(img, (45, 45), 25)
    pil_img = Image.fromarray(cv2.cvtColor(blurred, cv2.COLOR_BGR2RGB))
    buf = io.BytesIO()
    pil_img.save(buf, format="JPEG")
    return buf.getvalue()

def run_verification():
    print("=" * 75)
    print("PLANTSCANAI SECTION 12 E2E VERIFICATION TEST")
    print("=" * 75)

    # -------------------------------------------------------------
    # CASE A: Non-Plant Image (Photo of a car)
    # -------------------------------------------------------------
    print("\n--- CASE A: Non-Plant Image (Photo of a Car) ---")
    car_bytes = create_car_image_bytes()
    resp_a = client.post(
        "/api/v1/predict",
        files={"file": ("car_sample.jpg", car_bytes, "image/jpeg")},
    )
    print(f"HTTP Status Code: {resp_a.status_code}")
    data_a = resp_a.json()
    print(f"Response Payload:\n{data_a}")

    assert resp_a.status_code == 422, f"Expected 422 but got {resp_a.status_code}"
    assert data_a.get("success") is False
    assert data_a.get("error_code") == "NON_PLANT_IMAGE"
    assert "The uploaded image does not appear to contain a plant" in data_a.get("message", "")
    assert data_a.get("prediction") is None
    print(">>> CASE A VERIFIED: Non-plant image rejected with 422 and exact required message. No disease prediction returned.")

    # -------------------------------------------------------------
    # CASE B: Valid Plant Image (Clear tomato leaf)
    # -------------------------------------------------------------
    print("\n--- CASE B: Valid Plant Image (Tomato Leaf) ---")
    tomato_bytes, sample_path = get_real_tomato_leaf_bytes()
    print(f"Using tomato specimen: {sample_path}")
    resp_b = client.post(
        "/api/v1/predict",
        files={"file": ("tomato_leaf.jpg", tomato_bytes, "image/jpeg")},
    )
    print(f"HTTP Status Code: {resp_b.status_code}")
    data_b = resp_b.json()
    print(f"Predicted Class: {data_b.get('predicted_class')}")
    print(f"Display Name: {data_b.get('display_name')}")
    print(f"Confidence: {data_b.get('confidence')}")
    print(f"Plant Health Score: {data_b.get('plant_health_score')}")
    print(f"Treatment Summary: {data_b.get('recommendation', {}).get('summary')[:80]}...")

    assert resp_b.status_code == 200, f"Expected 200 but got {resp_b.status_code}"
    assert data_b.get("predicted_class") is not None
    assert data_b.get("confidence") is not None
    assert data_b.get("recommendation") is not None
    print(">>> CASE B VERIFIED: Plant validation passed and disease classifier executed normally.")

    # -------------------------------------------------------------
    # CASE C: Ambiguous Image (Very blurry image)
    # -------------------------------------------------------------
    print("\n--- CASE C: Ambiguous Image (Very Blurry Image) ---")
    blurry_bytes = create_blurry_image_bytes()
    resp_c = client.post(
        "/api/v1/predict",
        files={"file": ("blurry_sample.jpg", blurry_bytes, "image/jpeg")},
    )
    print(f"HTTP Status Code: {resp_c.status_code}")
    data_c = resp_c.json()
    print(f"Response Payload:\n{data_c}")

    assert resp_c.status_code == 422, f"Expected 422 but got {resp_c.status_code}"
    assert data_c.get("success") is False
    assert data_c.get("error_code") in ("BLURRY_IMAGE", "AMBIGUOUS_IMAGE")
    assert data_c.get("prediction") is None
    print(">>> CASE C VERIFIED: Ambiguous/blurry image rejected requesting clarification rather than inventing a disease.")

    # -------------------------------------------------------------
    # CASE D: Corrupted Image
    # -------------------------------------------------------------
    print("\n--- CASE D: Corrupted Image ---")
    corrupt_bytes = b"NOT_A_VALID_JPEG_HEADER_CORRUPTED_STREAM_DATA"
    resp_d = client.post(
        "/api/v1/predict",
        files={"file": ("corrupt.jpg", corrupt_bytes, "image/jpeg")},
    )
    print(f"HTTP Status Code: {resp_d.status_code}")
    data_d = resp_d.json()
    print(f"Response Payload:\n{data_d}")

    assert resp_d.status_code == 400, f"Expected 400 but got {resp_d.status_code}"
    assert data_d.get("error_code") in ("UNIDENTIFIED_IMAGE", "CORRUPTED_IMAGE")
    print(">>> CASE D VERIFIED: Corrupted image returned controlled 400 error without crashing.")

    print("\n" + "=" * 75)
    print("ALL 4 VERIFICATION CASES (A, B, C, D) PASSED WITH 100% COMPLIANCE!")
    print("=" * 75)

if __name__ == "__main__":
    run_verification()
