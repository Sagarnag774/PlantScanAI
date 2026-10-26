"""
Unit and regression tests for Plant-Part Dataset Quality Audit and Cleanup Pipeline
Verifies audit script feature extraction, directory structure, cryptographic split
leakage prevention, quarantine integrity, and original dataset preservation.
"""

import io
import json
from pathlib import Path
from PIL import Image
import numpy as np
import pytest

from datasets.scripts.audit_plant_parts_dataset import (
    analyze_image_features,
    automated_screen,
    compute_sha256,
    compute_dhash,
    audit_dataset,
    DATASET_DIR,
    CLEANED_DIR,
    QUARANTINE_DIR,
    REPORTS_DIR,
)

PROJECT_ROOT = Path(__file__).resolve().parents[2]


def test_feature_extraction_clean_synthetic_photo():
    """Test feature extraction on synthetic high-variance textured natural patch."""
    # Synthetic textured green patch
    np.random.seed(42)
    img_arr = np.random.randint(60, 160, (224, 224, 3), dtype=np.uint8)
    img_arr[:, :, 1] = np.clip(img_arr[:, :, 1] + 50, 0, 255)  # Green tint

    buf = io.BytesIO()
    Image.fromarray(img_arr).save(buf, format="JPEG")
    raw = buf.getvalue()

    features = analyze_image_features(raw)
    assert not features["corrupt"]
    assert features["width"] == 224
    assert features["height"] == 224
    assert features["paper_ratio"] < 0.10
    assert features["lap_var"] > 50.0

    status, cat, _ = automated_screen(features, "leaf")
    assert status == "keep"
    assert cat == "confirmed_photograph"


def test_feature_extraction_synthetic_drawing():
    """Test detection of monochrome line drawing on uniform paper background."""
    # 224x224 white paper background (V=255, S=0) with black line strokes
    img_arr = np.full((224, 224, 3), 250, dtype=np.uint8)
    # Add black line strokes (mimicking pencil sketch / diagram)
    img_arr[50:52, 20:200] = 0
    img_arr[100:102, 20:200] = 0
    img_arr[150:152, 20:200] = 0

    buf = io.BytesIO()
    Image.fromarray(img_arr).save(buf, format="JPEG")
    raw = buf.getvalue()

    features = analyze_image_features(raw)
    assert not features["corrupt"]
    assert features["paper_ratio"] > 0.80
    assert features["sat_mean"] < 5.0

    status, cat, _ = automated_screen(features, "stem")
    assert status == "reject"
    assert cat in ["scanned_document_text", "illustration_or_drawing"]


def test_feature_extraction_corrupted_file():
    """Test graceful handling of corrupt byte sequence."""
    corrupt_bytes = b"NOT_A_VALID_IMAGE_HEADER_XYZ123"
    features = analyze_image_features(corrupt_bytes)
    assert features["corrupt"] is True
    status, cat, reason = automated_screen(features, "fruit")
    assert status == "reject"
    assert cat == "corrupt_file"


def test_original_dataset_structure_and_preservation():
    """Verify that original datasets/plant_parts/ remains strictly intact with all 397 files."""
    assert DATASET_DIR.exists(), f"Original dataset dir missing: {DATASET_DIR}"

    expected_splits = ["train", "val", "test"]
    expected_classes = ["bark", "fruit", "leaf", "stem"]

    total_files = 0
    for s in expected_splits:
        for c in expected_classes:
            d = DATASET_DIR / s / c
            assert d.exists(), f"Missing split/class dir: {d}"
            files = list(d.glob("*.jpg")) + list(d.glob("*.png"))
            assert len(files) > 0, f"Empty directory: {d}"
            total_files += len(files)

    # Strictly verify all 397 original images are preserved
    assert total_files == 397, f"Original file count changed! Expected 397, got {total_files}"


def test_zero_cross_split_duplicate_leakage():
    """Verify that there is zero cryptographic SHA-256 duplicate leakage between splits."""
    audit_res = audit_dataset(DATASET_DIR)
    leakage = audit_res["cross_split_leakage"]
    assert len(leakage) == 0, f"Cross-split duplicate leakage detected: {leakage}"


def test_cleaned_dataset_and_quarantine_integrity():
    """Verify that cleaned dataset contains only valid photos and quarantine matches manifest."""
    assert CLEANED_DIR.exists(), f"Cleaned dataset dir missing: {CLEANED_DIR}"
    assert QUARANTINE_DIR.exists(), f"Quarantine dir missing: {QUARANTINE_DIR}"

    manifest_path = QUARANTINE_DIR / "quarantine_manifest.json"
    assert manifest_path.exists(), "Quarantine manifest missing!"

    with open(manifest_path, "r", encoding="utf-8") as f:
        manifest = json.load(f)

    # Every quarantined item must exist on disk and in manifest
    assert len(manifest) == 156, f"Expected 156 quarantined items post manual review, got {len(manifest)}"

    for item in manifest:
        q_file = QUARANTINE_DIR / item["quarantine_path"]
        assert q_file.exists(), f"Quarantined file missing on disk: {q_file}"
        assert item["decision"] in ["reject", "manual_review"]
        assert len(item["reason"]) > 5

    # Every cleaned file must be a readable image and traceable to original
    cleaned_files = list(CLEANED_DIR.rglob("*.jpg")) + list(CLEANED_DIR.rglob("*.png"))
    assert len(cleaned_files) == 241, f"Expected 241 retained photos post manual review, got {len(cleaned_files)}"
    assert len(cleaned_files) + len(manifest) == 397, "Total cleaned + quarantined must equal original 397 images"

    for cf in cleaned_files:
        rel = cf.relative_to(CLEANED_DIR)
        orig_file = DATASET_DIR / rel
        assert orig_file.exists(), f"Cleaned file {rel} not found in original dataset!"
        with Image.open(cf) as im:
            assert im.size == (224, 224)


def test_audit_reports_generated():
    """Verify inventory and audit report files are generated and structurally valid."""
    inv_file = REPORTS_DIR / "plant_parts_inventory.json"
    audit_file = REPORTS_DIR / "plant_parts_audit_report.json"
    contact_dir = REPORTS_DIR / "contact_sheets"

    assert inv_file.exists(), "Inventory JSON missing"
    assert audit_file.exists(), "Audit report JSON missing"
    assert contact_dir.exists(), "Contact sheets directory missing"

    with open(audit_file, "r", encoding="utf-8") as f:
        data = json.load(f)
    assert "summary" in data
    assert "audit_records" in data
    assert len(data["audit_records"]) == 397

    # Verify contact sheets exist for all 12 combinations
    contact_sheets = list(contact_dir.glob("*.jpg"))
    assert len(contact_sheets) == 12, f"Expected 12 contact sheets, got {len(contact_sheets)}"
