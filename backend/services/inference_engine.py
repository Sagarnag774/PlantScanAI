import os
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import numpy as np
from PIL import Image

from ..config import settings


@dataclass
class ModelPrediction:
    predicted_class: str
    crop: str
    confidence: float
    is_healthy: bool
    plant_part: str = "Leaf"
    display_name: str = ""
    top_k: List[Dict[str, float]] = field(default_factory=list)
    raw_probabilities: Optional[List[float]] = None


class BaseModelEngine(ABC):
    """Abstract interface for PlantScan AI model inference engines."""

    @abstractmethod
    def predict(
        self,
        image_array: np.ndarray,
        crop_hint: Optional[str] = None,
        plant_part_hint: Optional[str] = None,
        force_simulation: Optional[Dict[str, any]] = None,
    ) -> ModelPrediction:
        """Runs model inference on preprocessed image array."""
        pass

    @property
    @abstractmethod
    def engine_name(self) -> str:
        pass


class MockModelEngine(BaseModelEngine):
    """
    Deterministic inference engine used for API testing, frontend integration,
    and fallback when trained model weights are not loaded.
    Simulates predictions strictly adhering to the project's taxonomy.
    """

    TOMATO_CLASSES = [
        ("tomato_early_blight", "Tomato Early Blight", False),
        ("tomato_late_blight", "Tomato Late Blight", False),
        ("tomato_bacterial_spot", "Tomato Bacterial Spot", False),
        ("tomato_septoria_leaf_spot", "Tomato Septoria Leaf Spot", False),
        ("tomato_leaf_mold", "Tomato Leaf Mold", False),
        ("tomato_spider_mites", "Tomato Two-Spotted Spider Mites", False),
        ("tomato_target_spot", "Tomato Target Spot", False),
        ("tomato_yellow_leaf_curl_virus", "Tomato Yellow Leaf Curl Virus", False),
        ("tomato_mosaic_virus", "Tomato Mosaic Virus", False),
        ("tomato_healthy", "Healthy Tomato Plant", True),
    ]

    CROP_CLASS_MAP = {
        "tomato": TOMATO_CLASSES,
        "potato": [
            ("potato_early_blight", "Potato Early Blight", False),
            ("potato_late_blight", "Potato Late Blight", False),
            ("potato_healthy", "Healthy Potato", True),
        ],
        "rice": [
            ("bacterial_leaf_blight", "Rice Bacterial Leaf Blight", False),
            ("brown_spot", "Rice Brown Spot", False),
            ("leaf_blast", "Rice Leaf Blast", False),
            ("leaf_scald", "Rice Leaf Scald", False),
            ("sheath_blight", "Rice Sheath Blight", False),
            ("healthy_rice_leaf", "Healthy Rice Crop", True),
        ],
        "banana": [
            ("cordana", "Banana Cordana Leaf Spot", False),
            ("pestalotiopsis", "Banana Pestalotiopsis Leaf Spot", False),
            ("sigatoka", "Banana Yellow/Black Sigatoka", False),
            ("banana_healthy", "Healthy Banana Plant", True),
        ],
        "cotton": [
            ("bacterial_blight", "Cotton Bacterial Blight", False),
            ("curl_virus", "Cotton Leaf Curl Virus", False),
            ("fusarium_wilt", "Cotton Fusarium Wilt", False),
            ("cotton_healthy", "Healthy Cotton Crop", True),
        ],
        "mango": [
            ("anthracnose", "Mango Anthracnose", False),
            ("bacterial_canker", "Mango Bacterial Canker", False),
            ("die_back", "Mango Die Back", False),
            ("powdery_mildew", "Mango Powdery Mildew", False),
            ("sooty_mould", "Mango Sooty Mould", False),
            ("cutting_weevil", "Mango Leaf Cutting Weevil", False),
            ("gall_midge", "Mango Leaf Gall Midge", False),
            ("mango_healthy", "Healthy Mango Tree", True),
        ],
    }

    def __init__(self):
        self._name = "MockModelEngine (Simulation Mode)"

    @property
    def engine_name(self) -> str:
        return self._name

    def predict(
        self,
        image_array: np.ndarray,
        crop_hint: Optional[str] = None,
        plant_part_hint: Optional[str] = None,
        force_simulation: Optional[Dict[str, any]] = None,
    ) -> ModelPrediction:
        # Check for explicit simulation overrides (e.g. from unit test headers or mock parameters)
        if force_simulation:
            forced_class = force_simulation.get("class", "tomato_early_blight")
            forced_conf = float(force_simulation.get("confidence", 0.94))
            forced_crop = force_simulation.get("crop", "Tomato")
            is_healthy = "healthy" in forced_class
            return ModelPrediction(
                predicted_class=forced_class,
                crop=forced_crop,
                confidence=forced_conf,
                is_healthy=is_healthy,
                plant_part=plant_part_hint or "Leaf",
                display_name=forced_class.replace("_", " ").title(),
                top_k=[{"class": forced_class, "confidence": forced_conf}],
            )

        # Unsupported crop check if crop_hint provided but unknown
        if crop_hint:
            c_clean = crop_hint.strip().lower()
            if c_clean not in self.CROP_CLASS_MAP:
                return ModelPrediction(
                    predicted_class="unsupported_crop",
                    crop=crop_hint.capitalize(),
                    confidence=0.15,
                    is_healthy=False,
                    plant_part=plant_part_hint or "Unknown",
                    display_name="Unsupported Crop",
                    top_k=[],
                )
            target_crop = c_clean
        else:
            target_crop = "tomato"

        classes = self.CROP_CLASS_MAP[target_crop]

        # Deterministic simulation hash based on image mean and standard deviation
        img_mean = float(np.mean(image_array))
        img_std = float(np.std(image_array))
        hash_val = int((img_mean * 1000 + img_std * 500) * 100) % len(classes)

        chosen_class, display_name, is_healthy = classes[hash_val]

        # Calculate a realistic high confidence unless image variance is extremely low (e.g. blank image)
        if img_std < 0.05:
            # Low variance image (e.g. pure blank/solid color) -> low confidence / uncertain
            confidence = round(0.35 + (img_std * 2.0), 4)
        else:
            confidence = round(0.85 + (hash_val % 10) * 0.012, 4)
            confidence = min(0.98, max(0.72, confidence))

        top_k = [
            {"class": chosen_class, "confidence": confidence},
            {"class": classes[(hash_val + 1) % len(classes)][0], "confidence": round((1.0 - confidence) * 0.7, 4)},
            {"class": classes[(hash_val + 2) % len(classes)][0], "confidence": round((1.0 - confidence) * 0.3, 4)},
        ]

        return ModelPrediction(
            predicted_class=chosen_class,
            crop=target_crop.capitalize(),
            confidence=confidence,
            is_healthy=is_healthy,
            plant_part=plant_part_hint or "Leaf",
            display_name=display_name,
            top_k=top_k,
        )


class TFLiteModelEngine(BaseModelEngine):
    """
    TensorFlow Lite model inference engine for mobile-grade lightweight deployment.
    """

    def __init__(self, model_path: Path):
        self.model_path = model_path
        self._interpreter = None
        self._input_details = None
        self._output_details = None
        self._load_model()

    def _load_model(self):
        try:
            import tensorflow as tf
            self._interpreter = tf.lite.Interpreter(model_path=str(self.model_path))
            self._interpreter.allocate_tensors()
            self._input_details = self._interpreter.get_input_details()
            self._output_details = self._interpreter.get_output_details()
        except Exception as e:
            raise RuntimeError(f"Failed to load TFLite model at {self.model_path}: {e}")

    @property
    def engine_name(self) -> str:
        return f"TFLiteModelEngine ({self.model_path.name})"

    def predict(
        self,
        image_array: np.ndarray,
        crop_hint: Optional[str] = None,
        plant_part_hint: Optional[str] = None,
        force_simulation: Optional[Dict[str, any]] = None,
    ) -> ModelPrediction:
        self._interpreter.set_tensor(self._input_details[0]["index"], image_array)
        self._interpreter.invoke()
        output_data = self._interpreter.get_tensor(self._output_details[0]["index"])
        probs = output_data[0]
        max_idx = int(np.argmax(probs))
        confidence = float(probs[max_idx])
        # Return mapped class
        return ModelPrediction(
            predicted_class=str(max_idx),
            crop=crop_hint or "Tomato",
            confidence=confidence,
            is_healthy=False,
            plant_part=plant_part_hint or "Leaf",
        )


# Singleton instance manager
_engine_instance: Optional[BaseModelEngine] = None


def get_inference_engine() -> BaseModelEngine:
    global _engine_instance
    if _engine_instance is None:
        # Check if tflite model exists in weights dir
        tflite_path = settings.WEIGHTS_DIR / "disease_classifier.tflite"
        if tflite_path.exists():
            try:
                _engine_instance = TFLiteModelEngine(tflite_path)
            except Exception as e:
                print(f"Notice: TFLite engine initialization skipped ({e}), falling back to MockModelEngine.")
                _engine_instance = MockModelEngine()
        else:
            _engine_instance = MockModelEngine()
    return _engine_instance
