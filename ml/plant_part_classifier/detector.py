import json
import os
import threading
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Union

import cv2
import numpy as np
from PIL import Image

PROJECT_ROOT = Path(__file__).resolve().parents[2]
WEIGHTS_PATH = PROJECT_ROOT / "ml" / "weights" / "plant_part_classifier" / "plant_part_model.tflite"
CLASSES_PATH = PROJECT_ROOT / "ml" / "weights" / "plant_part_classifier" / "classes.json"


class PlantPartClassifier:
    """
    Stage 1 Deep Learning MobileNetV2 Plant-Part Classifier.
    Classifies uploaded plant images into 4 authoritative anatomical parts:
    - Leaf (Foliar tissue)
    - Stem (Stalks, branches, twigs, sheaths)
    - Fruit (Berries, drupes, pomes, pepos)
    - Bark (Tree trunk, woody outer periderm)

    Uses MobileNetV2 transfer-learning TFLite inference with graceful heuristic fallback.
    """

    SUPPORTED_PARTS = ["Leaf", "Stem", "Fruit", "Bark"]
    _interpreter = None
    _input_details = None
    _output_details = None
    _labels = ["bark", "fruit", "leaf", "stem"]
    _lock = threading.Lock()
    _initialized = False

    @classmethod
    def _init_model(cls) -> bool:
        with cls._lock:
            if cls._initialized:
                return cls._interpreter is not None
            cls._initialized = True

            if not WEIGHTS_PATH.exists():
                return False

            try:
                import tensorflow as tf
                cls._interpreter = tf.lite.Interpreter(model_path=str(WEIGHTS_PATH))
                cls._interpreter.allocate_tensors()
                cls._input_details = cls._interpreter.get_input_details()
                cls._output_details = cls._interpreter.get_output_details()

                if CLASSES_PATH.exists():
                    try:
                        with open(CLASSES_PATH, "r", encoding="utf-8") as f:
                            cls._labels = json.load(f)
                    except Exception:
                        pass
                return True
            except Exception as e:
                print(f"Notice: PlantPartClassifier TFLite init failed ({e}), using heuristic.")
                cls._interpreter = None
                return False

    @classmethod
    def classify(
        cls,
        image: Union[Image.Image, np.ndarray],
        crop_hint: Optional[str] = None,
    ) -> Tuple[str, float]:
        """
        Classifies dominant plant anatomical part.
        Returns: (part_name, confidence_score) where part_name in ['Leaf', 'Stem', 'Fruit', 'Bark'].
        """
        part_name, conf, _ = cls.classify_with_probabilities(image, crop_hint=crop_hint)
        return part_name, conf

    @classmethod
    def classify_with_probabilities(
        cls,
        image: Union[Image.Image, np.ndarray],
        crop_hint: Optional[str] = None,
    ) -> Tuple[str, float, Dict[str, float]]:
        """
        Performs Stage 1 inference and returns (dominant_part, confidence, all_probabilities).
        """
        # Convert to RGB uint8 2D image
        if isinstance(image, Image.Image):
            rgb = np.array(image.convert("RGB"))
        elif isinstance(image, np.ndarray):
            img_2d = image[0] if image.ndim == 4 else image
            if img_2d.dtype != np.uint8:
                if img_2d.min() < 0:
                    img_2d = ((img_2d + 1.0) * 127.5).clip(0, 255).astype(np.uint8)
                elif img_2d.max() <= 1.0:
                    img_2d = (img_2d * 255.0).clip(0, 255).astype(np.uint8)
                else:
                    img_2d = img_2d.astype(np.uint8)
            rgb = img_2d
        else:
            return "Leaf", 0.85, {"leaf": 0.85, "fruit": 0.05, "stem": 0.05, "bark": 0.05}

        # 1. Run Deep Learning TFLite Model if loaded
        if cls._init_model() and cls._interpreter is not None:
            try:
                # Preprocess: resize to 224x224 float32 [0, 255] (model contains internal preprocess_input)
                pil_im = Image.fromarray(rgb).resize((224, 224), Image.Resampling.BILINEAR)
                input_data = np.expand_dims(np.array(pil_im, dtype=np.float32), axis=0)

                with cls._lock:
                    cls._interpreter.set_tensor(cls._input_details[0]["index"], input_data)
                    cls._interpreter.invoke()
                    probs = cls._output_details[0]
                    output_data = cls._interpreter.get_tensor(probs["index"])[0]

                prob_dict = {
                    cls._labels[i].capitalize(): round(float(output_data[i]), 4)
                    for i in range(len(cls._labels))
                }
                max_idx = int(np.argmax(output_data))
                best_label = cls._labels[max_idx].capitalize()
                best_conf = round(float(output_data[max_idx]), 4)

                return best_label, best_conf, prob_dict
            except Exception as e:
                print(f"Notice: Stage 1 TFLite inference exception ({e}), falling back to heuristic.")

        # 2. Heuristic Fallback
        part, conf = cls._heuristic_classify(rgb, crop_hint=crop_hint)
        prob_dict = {p: 0.10 for p in cls.SUPPORTED_PARTS}
        prob_dict[part] = conf
        return part, conf, prob_dict

    @classmethod
    def _heuristic_classify(cls, rgb: np.ndarray, crop_hint: Optional[str] = None) -> Tuple[str, float]:
        h, w, _ = rgb.shape
        total_pixels = h * w

        hsv = cv2.cvtColor(rgb, cv2.COLOR_RGB2HSV)
        gray = cv2.cvtColor(rgb, cv2.COLOR_RGB2GRAY)

        green_mask = cv2.inRange(hsv, (35, 30, 40), (88, 255, 255))
        green_ratio = np.count_nonzero(green_mask) / total_pixels

        red_mask1 = cv2.inRange(hsv, (0, 45, 50), (18, 255, 255))
        red_mask2 = cv2.inRange(hsv, (162, 45, 50), (180, 255, 255))
        yellow_mask = cv2.inRange(hsv, (18, 40, 50), (35, 255, 255))
        purple_mask = cv2.inRange(hsv, (125, 40, 30), (155, 255, 200))
        fruit_color_mask = cv2.bitwise_or(cv2.bitwise_or(red_mask1, red_mask2), cv2.bitwise_or(yellow_mask, purple_mask))
        fruit_color_ratio = np.count_nonzero(fruit_color_mask) / total_pixels

        brown_mask = cv2.inRange(hsv, (10, 30, 20), (25, 180, 140))
        brown_ratio = np.count_nonzero(brown_mask) / total_pixels

        blurred = cv2.GaussianBlur(gray, (11, 11), 0)
        edges = cv2.Canny(blurred, 30, 100)
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (7, 7))
        closed_edges = cv2.morphologyEx(edges, cv2.MORPH_CLOSE, kernel)
        contours, _ = cv2.findContours(closed_edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        max_area = 0
        best_circularity = 0.0
        best_solidity = 0.0
        best_aspect_ratio = 1.0

        for cnt in contours:
            area = cv2.contourArea(cnt)
            if area > max_area and area > (total_pixels * 0.08):
                max_area = area
                perimeter = cv2.arcLength(cnt, True)
                if perimeter > 0:
                    best_circularity = (4 * np.pi * area) / (perimeter * perimeter)
                hull = cv2.convexHull(cnt)
                hull_area = cv2.contourArea(hull)
                if hull_area > 0:
                    best_solidity = float(area) / hull_area
                x, y, bw, bh = cv2.boundingRect(cnt)
                best_aspect_ratio = max(bw, bh) / max(1, min(bw, bh))

        # Check for bark texture (high edge complexity with low green ratio and earthy tones)
        edge_density = np.count_nonzero(edges) / total_pixels
        if brown_ratio > 0.35 and green_ratio < 0.15 and edge_density > 0.08:
            return "Bark", 0.88

        # Fruit detection
        if (best_circularity > 0.45 and best_solidity > 0.75) or fruit_color_ratio > 0.20:
            return "Fruit", 0.85

        # Stem detection
        if best_aspect_ratio > 2.2 and green_ratio < 0.35:
            return "Stem", 0.82

        return "Leaf", 0.90
