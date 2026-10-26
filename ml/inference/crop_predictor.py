
"""
PlantScan AI - Multi-Crop Disease Predictor (Inference Interface)

Provides a unified CropDiseasePredictor for image preprocessing,
Keras/TFLite inference, class mapping, and confidence thresholding.
"""

import argparse
import json
from pathlib import Path
from typing import Any, Dict, Optional, Union

import numpy as np
from PIL import Image
import tensorflow as tf


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_WEIGHTS_DIR = PROJECT_ROOT / "ml" / "weights"

IMG_SIZE = (224, 224)
CONFIDENCE_THRESHOLD = 0.70

SUPPORTED_CROPS = [
    "apple",
    "banana",
    "bell_pepper",
    "cotton",
    "grape",
    "maize",
    "mango",
    "potato",
    "rice",
    "tomato",
]


class CropDiseasePredictor:
    def __init__(
        self,
        crop: str = "tomato",
        model_path: Optional[Union[str, Path]] = None,
        use_tflite: bool = True,
        confidence_threshold: float = CONFIDENCE_THRESHOLD,
    ):
        self.crop = crop.strip().lower().replace(" ", "_")

        if self.crop not in SUPPORTED_CROPS:
            raise ValueError(
                f"Unsupported crop '{self.crop}'. "
                f"Supported crops: {SUPPORTED_CROPS}"
            )

        if not 0.0 <= confidence_threshold <= 1.0:
            raise ValueError(
                "confidence_threshold must be between 0.0 and 1.0"
            )

        self.use_tflite = use_tflite
        self.confidence_threshold = confidence_threshold

        crop_weights_dir = DEFAULT_WEIGHTS_DIR / self.crop

        if use_tflite:
            if model_path is None:
                candidate = crop_weights_dir / f"{self.crop}_model.tflite"

                if candidate.exists():
                    model_path = candidate
                else:
                    model_path = (
                        DEFAULT_WEIGHTS_DIR / "disease_classifier.tflite"
                    )

            self.model_path = Path(model_path)

            if not self.model_path.exists():
                raise FileNotFoundError(
                    f"TFLite model missing for '{self.crop}': "
                    f"{self.model_path}"
                )

            print(
                f"Loading TFLite Interpreter for {self.crop.upper()}: "
                f"{self.model_path}"
            )

            self.interpreter = tf.lite.Interpreter(
                model_path=str(self.model_path)
            )
            self.interpreter.allocate_tensors()

            self.input_details = self.interpreter.get_input_details()
            self.output_details = self.interpreter.get_output_details()
            self.model = None

            if len(self.input_details) != 1:
                raise ValueError(
                    "Expected a single-input TFLite model, but found "
                    f"{len(self.input_details)} inputs."
                )

            self.input_detail = self.input_details[0]

        else:
            if model_path is None:
                model_path = (
                    crop_weights_dir / f"{self.crop}_mobilenetv2.keras"
                )

            self.model_path = Path(model_path)

            if not self.model_path.exists():
                raise FileNotFoundError(
                    f"Keras model missing for '{self.crop}': "
                    f"{self.model_path}"
                )

            print(
                f"Loading Keras Model Engine for {self.crop.upper()}: "
                f"{self.model_path}"
            )

            self.model = tf.keras.models.load_model(self.model_path)
            self.interpreter = None
            self.input_detail = None

        # Load class names in the order used during model training.
        classes_json = crop_weights_dir / "classes.json"
        train_dir = (
            PROJECT_ROOT / "datasets" / "model" / self.crop / "train"
        )

        if classes_json.exists():
            with open(classes_json, "r", encoding="utf-8") as file:
                self.class_names = json.load(file)
        elif train_dir.exists():
            self.class_names = sorted(
                directory.name
                for directory in train_dir.iterdir()
                if directory.is_dir()
            )
        else:
            raise FileNotFoundError(
                f"Class mapping not found for '{self.crop}'. Expected "
                f"{classes_json} or training directory {train_dir}."
            )

        if not isinstance(self.class_names, list) or not self.class_names:
            raise ValueError(
                f"Invalid or empty class mapping: {classes_json}"
            )

        if not all(isinstance(name, str) for name in self.class_names):
            raise ValueError(
                f"Class mapping must contain only strings: {classes_json}"
            )

        # Verify that the class count matches the model output count.
        if self.use_tflite:
            output_shape = self.output_details[0]["shape"]
        else:
            output_shape = self.model.output_shape

        if isinstance(output_shape, list):
            raise ValueError(
                "Multiple model outputs are not supported by this predictor."
            )

        output_class_count = int(output_shape[-1])

        if output_class_count != len(self.class_names):
            raise ValueError(
                f"Model outputs {output_class_count} classes, but "
                f"{len(self.class_names)} class names were loaded for "
                f"'{self.crop}'. Verify the model and classes.json belong "
                "to the same training run."
            )

    def preprocess_image(
        self,
        image_input: Union[str, Path, Image.Image, np.ndarray],
    ) -> np.ndarray:
        """Convert an image to the MobileNetV2 inference input tensor."""

        if isinstance(image_input, (str, Path)):
            with Image.open(image_input) as image:
                img = image.convert("RGB")

        elif isinstance(image_input, np.ndarray):
            if image_input.dtype != np.uint8:
                raise ValueError(
                    "NumPy image inputs must use uint8 values in the "
                    "range 0-255. Convert other image formats explicitly."
                )
            img = Image.fromarray(image_input).convert("RGB")

        elif isinstance(image_input, Image.Image):
            img = image_input.convert("RGB")

        else:
            raise ValueError(
                f"Unsupported image input type: {type(image_input)}"
            )

        img = img.resize(IMG_SIZE)

        # Pixel values start in [0, 255].
        img_array = np.asarray(img, dtype=np.float32)

        # Match MobileNetV2 preprocessing used during training.
        # This scales RGB pixel values to approximately [-1, 1].
        img_array = tf.keras.applications.mobilenet_v2.preprocess_input(
            img_array
        )

        img_tensor = np.expand_dims(img_array, axis=0)

        return img_tensor.astype(np.float32, copy=False)

    def _prepare_model_input(self, img_tensor: np.ndarray) -> np.ndarray:
        """Validate and adapt the input tensor to the selected engine."""

        if not self.use_tflite:
            expected_shape = tuple(self.model.input_shape)

            if len(expected_shape) != 4:
                raise ValueError(
                    f"Expected a 4D Keras input shape, got {expected_shape}"
                )

            for actual, expected in zip(img_tensor.shape, expected_shape):
                if expected is not None and actual != expected:
                    raise ValueError(
                        f"Input shape {img_tensor.shape} does not match "
                        f"Keras model input shape {expected_shape}"
                    )

            return img_tensor

        detail = self.input_detail
        expected_shape = tuple(int(dim) for dim in detail["shape"])
        expected_dtype = detail["dtype"]

        # Resize dynamic or differently-sized batch input tensors when
        # the model supports resizing. Spatial dimensions must match.
        if len(expected_shape) != 4 or expected_shape[1:] != img_tensor.shape[1:]:
            raise ValueError(
                f"Unsupported TFLite input shape {expected_shape}; "
                f"expected a shape compatible with {img_tensor.shape}."
            )

        if expected_shape[0] != img_tensor.shape[0]:
            self.interpreter.resize_tensor_input(
                detail["index"],
                img_tensor.shape,
                strict=False,
            )
            self.interpreter.allocate_tensors()
            self.input_details = self.interpreter.get_input_details()
            self.output_details = self.interpreter.get_output_details()
            self.input_detail = self.input_details[0]
            detail = self.input_detail

        if np.issubdtype(expected_dtype, np.floating):
            return img_tensor.astype(expected_dtype, copy=False)

        # Quantized integer models need their input quantization parameters.
        scale, zero_point = detail["quantization"]

        if scale <= 0:
            raise ValueError(
                "TFLite model has integer inputs but no valid input "
                "quantization scale."
            )

        quantized = np.round(img_tensor / scale + zero_point)
        limits = np.iinfo(expected_dtype)
        return np.clip(quantized, limits.min, limits.max).astype(
            expected_dtype
        )

    def predict(
        self,
        image_input: Union[str, Path, Image.Image, np.ndarray],
    ) -> Dict[str, Any]:
        img_tensor = self.preprocess_image(image_input)
        model_input = self._prepare_model_input(img_tensor)

        if self.use_tflite:
            self.interpreter.set_tensor(
                self.input_detail["index"], model_input
            )
            self.interpreter.invoke()

            output_detail = self.output_details[0]
            output = self.interpreter.get_tensor(output_detail["index"])[0]

            # Dequantize integer output tensors when necessary.
            output_dtype = output_detail["dtype"]
            if np.issubdtype(output_dtype, np.integer):
                scale, zero_point = output_detail["quantization"]
                if scale > 0:
                    output = (output.astype(np.float32) - zero_point) * scale

            probs = np.asarray(output, dtype=np.float32)
        else:
            probs = np.asarray(
                self.model.predict(model_input, verbose=0)[0],
                dtype=np.float32,
            )

        if probs.ndim != 1 or len(probs) != len(self.class_names):
            raise ValueError(
                f"Unexpected model output shape {probs.shape}; "
                f"expected one score per class ({len(self.class_names)})."
            )

        if not np.all(np.isfinite(probs)):
            raise ValueError("Model output contains NaN or infinite values.")

        top_idx = int(np.argmax(probs))
        confidence = float(probs[top_idx])
        predicted_class = self.class_names[top_idx]

        is_healthy = "healthy" in predicted_class.lower()
        is_uncertain = confidence < self.confidence_threshold

        ranked_indices = np.argsort(probs)[::-1][: min(3, len(probs))]

        return {
            "crop": self.crop.capitalize(),
            "predicted_class": (
                predicted_class if not is_uncertain else "uncertain"
            ),
            "display_name": (
                predicted_class.replace("_", " ").title()
                if not is_uncertain
                else "Uncertain Diagnosis"
            ),
            "confidence": round(confidence, 4),
            "is_healthy": is_healthy,
            "status": "uncertain" if is_uncertain else "success",
            "confidence_threshold": self.confidence_threshold,
            "top_k": [
                {
                    "class": self.class_names[idx],
                    "confidence": round(float(probs[idx]), 4),
                }
                for idx in ranked_indices
            ],
        }


def main():
    parser = argparse.ArgumentParser(
        description="Run PlantScan AI crop disease prediction."
    )
    parser.add_argument(
        "--image",
        required=True,
        help="Path to input image file.",
    )
    parser.add_argument(
        "--crop",
        default="tomato",
        choices=SUPPORTED_CROPS,
        help="Target crop species.",
    )
    parser.add_argument(
        "--model-path",
        type=Path,
        default=None,
        help="Optional explicit path to a model file.",
    )
    parser.add_argument(
        "--use-tflite",
        action="store_true",
        help="Use the TFLite model engine.",
    )
    parser.add_argument(
        "--confidence-threshold",
        type=float,
        default=CONFIDENCE_THRESHOLD,
        help="Confidence threshold between 0 and 1.",
    )

    args = parser.parse_args()

    predictor = CropDiseasePredictor(
        crop=args.crop,
        model_path=args.model_path,
        use_tflite=args.use_tflite,
        confidence_threshold=args.confidence_threshold,
    )

    result = predictor.predict(args.image)

    print("\nPrediction Result:")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
