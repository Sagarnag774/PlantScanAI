"""
Unit tests for Stage 1 PlantPartClassifier
"""

import numpy as np
import pytest
from PIL import Image
from pathlib import Path

from ml.plant_part_classifier.detector import PlantPartClassifier

PROJECT_ROOT = Path(__file__).resolve().parents[2]


def test_supported_parts_list():
    parts = PlantPartClassifier.SUPPORTED_PARTS
    assert "Leaf" in parts
    assert "Stem" in parts
    assert "Fruit" in parts
    assert "Bark" in parts


def test_classify_dummy_leaf():
    # Green image
    arr = np.zeros((224, 224, 3), dtype=np.uint8)
    arr[:, :, 1] = 180  # green
    part, conf = PlantPartClassifier.classify(arr)
    assert part in PlantPartClassifier.SUPPORTED_PARTS
    assert 0.0 <= conf <= 1.0


def test_classify_dummy_bark():
    # Brown image
    arr = np.zeros((224, 224, 3), dtype=np.uint8)
    arr[:, :, 0] = 120  # R
    arr[:, :, 1] = 80   # G
    arr[:, :, 2] = 50   # B
    part, conf, probs = PlantPartClassifier.classify_with_probabilities(arr)
    assert part in PlantPartClassifier.SUPPORTED_PARTS
    assert isinstance(probs, dict)
    assert len(probs) >= 4


def test_classify_real_test_leaf_if_exists():
    leaf_dir = PROJECT_ROOT / "datasets" / "plant_parts" / "test" / "leaf"
    if leaf_dir.exists():
        imgs = list(leaf_dir.glob("*.jpg"))
        if imgs:
            im = Image.open(imgs[0])
            part, conf, probs = PlantPartClassifier.classify_with_probabilities(im)
            assert part == "Leaf"
            assert conf >= 0.50
