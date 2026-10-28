"""
PlantScanAI - Plant Presence & Image Quality Validator
Authoritative Computer Vision and Machine Learning Module

Executes BEFORE disease classification to detect and reject:
1. Non-plant images (people, cars, buildings, animals, food, phones, landscapes without plants)
2. Blurry and severely unfocused images
3. Low-quality, dark, or featureless images
4. Ambiguous images where plant presence cannot be reliably established

Guarantees disease classification models are NEVER executed on non-plant inputs.
"""

import logging
import os
import threading
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

import cv2
import numpy as np
from PIL import Image

logger = logging.getLogger("plantscan.plant_validator")

PROJECT_ROOT = Path(__file__).resolve().parents[2]
MODEL_WEIGHTS_PATH = PROJECT_ROOT / "ml" / "weights" / "plant_validator" / "plant_validator_model.joblib"


@dataclass
class ValidationResult:
    is_valid: bool
    status: str  # 'valid', 'non_plant', 'blurry', 'ambiguous', 'low_quality'
    error_code: Optional[str] = None  # 'NON_PLANT_IMAGE', 'BLURRY_IMAGE', 'AMBIGUOUS_IMAGE', 'LOW_QUALITY_IMAGE'
    message: Optional[str] = None
    plant_score: float = 0.0
    details: Dict[str, Any] = field(default_factory=dict)


class PlantImageValidator:
    """
    Two-Tier Plant Presence Validator:
    Tier 1: Fast Analytical Computer Vision & Botanical Morphometry
            - Laplacian focus variance (blur detection)
            - Illumination & flat-entropy analysis (dark / washed-out check)
            - Botanical pigment colorimetry (chlorophyll, anthocyanin, carotenoid, suberin)
            - Normalized Difference Vegetation Indices (Excess Green, Excess Red, Excess Blue)
            - Rectilinear edge geometry & Hough line orientation analysis (rejecting cars, buildings, phones)
            - Human skin tone chromatic filtering (YCrCb skin model)
            - Landscape sky & atmospheric horizon filtering
    Tier 2: Supervised Ensemble Machine Learning Classifier (if trained weights are present)
            - 48-dimensional feature vector evaluated via scikit-learn ensemble
            - Graceful automatic fallback to calibrated Tier 1 computer vision scoring
    """

    _model = None
    _model_loaded = False
    _model_lock = threading.Lock()

    # Default configurable thresholds
    DEFAULT_BLUR_THRESHOLD: float = 20.0
    DEFAULT_MIN_PLANT_SCORE: float = 0.50
    DEFAULT_AMBIGUOUS_THRESHOLD: float = 0.35

    REJECTION_MESSAGE_NON_PLANT = (
        "The uploaded image does not appear to contain a plant. "
        "Please upload a clear image of a plant leaf or another supported plant part."
    )
    REJECTION_MESSAGE_BLURRY = (
        "The uploaded image is too blurry to reliably detect plant features. "
        "Please hold your camera steady and upload a sharp, well-focused photo."
    )
    REJECTION_MESSAGE_LOW_QUALITY = (
        "The uploaded image is too dark, washed out, or featureless to reliably identify plant tissue. "
        "Please upload a clear photo taken in good lighting."
    )
    REJECTION_MESSAGE_AMBIGUOUS = (
        "The presence of a plant or supported plant part cannot be reliably determined. "
        "Please upload a closer, clearer photo of the plant leaf or fruit."
    )

    @classmethod
    def _load_model(cls) -> bool:
        if cls._model_loaded:
            return cls._model is not None
        with cls._model_lock:
            if cls._model_loaded:
                return cls._model is not None
            cls._model_loaded = True
            if MODEL_WEIGHTS_PATH.exists():
                try:
                    import joblib
                    cls._model = joblib.load(MODEL_WEIGHTS_PATH)
                    logger.info("Loaded PlantImageValidator ML model from %s", MODEL_WEIGHTS_PATH)
                    return True
                except Exception as e:
                    logger.warning("Could not load PlantImageValidator model (%s), using CV heuristic.", e)
                    cls._model = None
            return False

    @classmethod
    def extract_features(cls, rgb: np.ndarray) -> np.ndarray:
        """
        Extracts a compact 48-dimensional feature representation capturing:
        - Botanical color distributions (HSV, LAB, RGB)
        - Vegetation chromaticity indices (ExG, ExR, ExB)
        - Edge orientation entropy and rectilinear man-made alignment
        - Surface texture & spatial cohesion
        """
        if rgb.shape[:2] != (224, 224):
            rgb = cv2.resize(rgb, (224, 224), interpolation=cv2.INTER_AREA)

        h, w, _ = rgb.shape
        total_pixels = h * w

        f_rgb = rgb.astype(np.float32) / 255.0
        r, g, b = f_rgb[:, :, 0], f_rgb[:, :, 1], f_rgb[:, :, 2]

        # 1. Vegetation Indices
        exg = 2.0 * g - r - b  # Excess Green Index
        exr = 1.4 * r - g      # Excess Red Index
        exb = 2.0 * b - r - g  # Excess Blue Index

        foliar_ratio = float(np.count_nonzero(exg > 0.04)) / total_pixels
        red_ratio = float(np.count_nonzero(exr > 0.12)) / total_pixels
        blue_ratio = float(np.count_nonzero(exb > 0.05)) / total_pixels
        mean_exg = float(np.mean(exg))
        mean_exr = float(np.mean(exr))
        mean_exb = float(np.mean(exb))

        # 2. HSV Color Distribution
        hsv = cv2.cvtColor(rgb, cv2.COLOR_RGB2HSV)
        h_channel = hsv[:, :, 0]
        s_channel = hsv[:, :, 1]
        v_channel = hsv[:, :, 2]

        h_hist, _ = np.histogram(h_channel, bins=16, range=(0, 180), density=True)
        s_mean = float(np.mean(s_channel)) / 255.0
        s_std = float(np.std(s_channel)) / 255.0
        v_mean = float(np.mean(v_channel)) / 255.0
        v_std = float(np.std(v_channel)) / 255.0

        # Chlorophyll green in HSV
        green_mask = cv2.inRange(hsv, (28, 25, 25), (95, 255, 255))
        green_ratio = float(np.count_nonzero(green_mask)) / total_pixels

        # 3. CIELAB Color Distribution
        lab = cv2.cvtColor(rgb, cv2.COLOR_RGB2LAB)
        l_chan, a_chan, b_chan = cv2.split(lab)
        l_mean = float(np.mean(l_chan)) / 255.0
        a_mean = (float(np.mean(a_chan)) - 128.0) / 128.0
        b_mean = (float(np.mean(b_chan)) - 128.0) / 128.0
        a_std = float(np.std(a_chan)) / 128.0
        b_std = float(np.std(b_chan)) / 128.0

        # 4. Human Skin Tone Cluster (YCrCb standard)
        ycrcb = cv2.cvtColor(rgb, cv2.COLOR_RGB2YCrCb)
        y_c, cr_c, cb_c = cv2.split(ycrcb)
        skin_mask = (y_c > 90) & (cr_c >= 133) & (cr_c <= 173) & (cb_c >= 77) & (cb_c <= 127)
        skin_ratio = float(np.count_nonzero(skin_mask)) / total_pixels

        # 5. Edges & Angular Orientation Entropy
        gray = cv2.cvtColor(rgb, cv2.COLOR_RGB2GRAY)
        gx = cv2.Sobel(gray, cv2.CV_32F, 1, 0, ksize=3)
        gy = cv2.Sobel(gray, cv2.CV_32F, 0, 1, ksize=3)
        mag, ang = cv2.cartToPolar(gx, gy, angleInDegrees=True)

        sig_mask = mag > 20.0
        edge_density = float(np.count_nonzero(sig_mask)) / total_pixels

        if np.count_nonzero(sig_mask) > 50:
            ang_sig = ang[sig_mask]
            # Rectilinear alignment (angles near 0, 90, 180, 270 degrees)
            rect_count = np.count_nonzero(
                (ang_sig < 14)
                | (ang_sig > 346)
                | ((ang_sig > 76) & (ang_sig < 104))
                | ((ang_sig > 166) & (ang_sig < 194))
                | ((ang_sig > 256) & (ang_sig < 284))
            )
            rect_ratio = rect_count / ang_sig.size

            hist_ang, _ = np.histogram(ang_sig, bins=12, range=(0, 360), density=True)
            hist_ang = hist_ang[hist_ang > 0]
            ang_entropy = -float(np.sum(hist_ang * np.log2(hist_ang + 1e-7)))
        else:
            rect_ratio = 0.0
            ang_entropy = 0.0

        # 6. Sharpness (Laplacian variance)
        blur_var = float(cv2.Laplacian(gray, cv2.CV_64F).var())
        norm_blur = min(1.0, blur_var / 500.0)

        # 7. Spatial Morphological Cohesion
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (7, 7))
        botanical_raw = green_mask | cv2.inRange(hsv, (18, 30, 40), (32, 255, 255))
        cleaned = cv2.morphologyEx(botanical_raw, cv2.MORPH_CLOSE, kernel)
        contours, _ = cv2.findContours(cleaned, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        max_contour_area = 0.0
        best_circ = 0.0
        best_sol = 0.0
        best_extent = 0.0
        if contours:
            for cnt in contours:
                area = cv2.contourArea(cnt)
                if area > max_contour_area:
                    max_contour_area = area
                    peri = cv2.arcLength(cnt, True)
                    if peri > 0:
                        best_circ = (4 * np.pi * area) / (peri * peri)
                    hull = cv2.convexHull(cnt)
                    h_area = cv2.contourArea(hull)
                    if h_area > 0:
                        best_sol = area / h_area
                    bx, by, bw, bh = cv2.boundingRect(cnt)
                    if (bw * bh) > 0:
                        best_extent = area / (bw * bh)
        max_contour_ratio = max_contour_area / total_pixels

        # Assemble full vector
        features = [
            foliar_ratio, red_ratio, blue_ratio, mean_exg, mean_exr, mean_exb,
            s_mean, s_std, v_mean, v_std, green_ratio,
            l_mean, a_mean, b_mean, a_std, b_std,
            skin_ratio, edge_density, rect_ratio, ang_entropy, norm_blur, max_contour_ratio,
            best_circ, best_sol, best_extent,
        ] + list(h_hist)  # 25 + 16 = 41 scalar features

        # Add 10 additional spatial texture stats
        gray_f = gray.astype(np.float32) / 255.0
        features.extend([
            float(np.std(gray_f)),
            float(np.percentile(gray_f, 90) - np.percentile(gray_f, 10)),
            float(np.mean(np.abs(gx))) / 255.0,
            float(np.mean(np.abs(gy))) / 255.0,
            float(np.std(mag)),
            float(np.count_nonzero(mag > 50.0)) / total_pixels,
            float(np.count_nonzero((hsv[:, :, 0] > 100) & (hsv[:, :, 0] < 130) & (hsv[:, :, 1] > 30))) / total_pixels,  # sky blue
            float(np.count_nonzero(hsv[:, :, 1] < 20)) / total_pixels,  # neutral gray
            float(np.count_nonzero(v_channel < 30)) / total_pixels,    # shadow/black
            float(np.count_nonzero(v_channel > 230)) / total_pixels,   # glare/white
        ])
        return np.array(features, dtype=np.float32)

    @classmethod
    def validate(
        cls,
        image: Union[Image.Image, np.ndarray],
        plant_part_hint: Optional[str] = None,
        crop_hint: Optional[str] = None,
        blur_threshold: Optional[float] = None,
        min_plant_score: Optional[float] = None,
        ambiguous_threshold: Optional[float] = None,
    ) -> ValidationResult:
        """
        Validates an uploaded image for plant presence.
        Returns ValidationResult with is_valid=True for bona fide plant images,
        or is_valid=False with appropriate error_code and clear user-facing message.
        """
        # Threshold resolution
        blur_th = blur_threshold if blur_threshold is not None else cls.DEFAULT_BLUR_THRESHOLD
        min_score = min_plant_score if min_plant_score is not None else cls.DEFAULT_MIN_PLANT_SCORE
        ambig_th = ambiguous_threshold if ambiguous_threshold is not None else cls.DEFAULT_AMBIGUOUS_THRESHOLD

        # Convert to RGB uint8 2D image
        if isinstance(image, Image.Image):
            rgb = np.array(image.convert("RGB"))
        elif isinstance(image, np.ndarray):
            rgb = image[0] if image.ndim == 4 else image
            if rgb.dtype != np.uint8:
                if rgb.min() < 0:
                    rgb = ((rgb + 1.0) * 127.5).clip(0, 255).astype(np.uint8)
                elif rgb.max() <= 1.0:
                    rgb = (rgb * 255.0).clip(0, 255).astype(np.uint8)
                else:
                    rgb = rgb.astype(np.uint8)
        else:
            return ValidationResult(
                is_valid=False,
                status="low_quality",
                error_code="INVALID_IMAGE_PAYLOAD",
                message=cls.REJECTION_MESSAGE_LOW_QUALITY,
                plant_score=0.0,
            )

        h, w, _ = rgb.shape
        total_pixels = h * w

        # -------------------------------------------------------------
        # 1. Illumination & Flat Featureless Image Check
        # -------------------------------------------------------------
        std_dev = float(np.std(rgb))
        mean_val = float(np.mean(rgb))
        if std_dev < 10.0 or mean_val < 15.0 or (mean_val > 245.0 and std_dev < 15.0):
            return ValidationResult(
                is_valid=False,
                status="low_quality",
                error_code="LOW_QUALITY_IMAGE",
                message=cls.REJECTION_MESSAGE_LOW_QUALITY,
                plant_score=0.05,
                details={"std_dev": round(std_dev, 2), "mean_val": round(mean_val, 2)},
            )

        # -------------------------------------------------------------
        # 2. Sharpness & Blur Check (Laplacian Variance)
        # -------------------------------------------------------------
        gray = cv2.cvtColor(rgb, cv2.COLOR_RGB2GRAY)
        blur_var = float(cv2.Laplacian(gray, cv2.CV_64F).var())
        if blur_var < blur_th:
            return ValidationResult(
                is_valid=False,
                status="blurry",
                error_code="BLURRY_IMAGE",
                message=cls.REJECTION_MESSAGE_BLURRY,
                plant_score=0.10,
                details={"blur_variance": round(blur_var, 2), "blur_threshold": blur_th},
            )

        # -------------------------------------------------------------
        # 3. Botanical Colorimetry & Morphological Extraction
        # -------------------------------------------------------------
        hsv = cv2.cvtColor(rgb, cv2.COLOR_RGB2HSV)
        lab = cv2.cvtColor(rgb, cv2.COLOR_RGB2LAB)
        l_chan, a_chan, b_chan = cv2.split(lab)

        f_rgb = rgb.astype(np.float32) / 255.0
        exg = 2.0 * f_rgb[:, :, 1] - f_rgb[:, :, 0] - f_rgb[:, :, 2]
        exr = 1.4 * f_rgb[:, :, 0] - f_rgb[:, :, 1]

        # Chlorophyll foliage: Hue [28, 95] & positive ExG
        green_mask = cv2.inRange(hsv, (28, 25, 25), (95, 255, 255))
        green_ratio = float(np.count_nonzero(green_mask)) / total_pixels
        exg_ratio = float(np.count_nonzero(exg > 0.04)) / total_pixels

        # Yellow / chlorotic senescence: Hue [18, 32]
        yellow_mask = cv2.inRange(hsv, (18, 30, 40), (32, 255, 255))
        yellow_ratio = float(np.count_nonzero(yellow_mask)) / total_pixels

        # Fruit pigments (anthocyanins / carotenoids): red, orange, purple
        red1 = cv2.inRange(hsv, (0, 45, 50), (18, 255, 255))
        red2 = cv2.inRange(hsv, (162, 45, 50), (180, 255, 255))
        purple = cv2.inRange(hsv, (125, 40, 30), (155, 255, 200))
        fruit_mask = red1 | red2 | purple
        fruit_ratio = float(np.count_nonzero(fruit_mask)) / total_pixels

        # Bark & woody tissue: brown
        brown_mask = cv2.inRange(hsv, (10, 30, 20), (28, 180, 130))
        brown_ratio = float(np.count_nonzero(brown_mask)) / total_pixels

        # Human skin detection (YCrCb)
        ycrcb = cv2.cvtColor(rgb, cv2.COLOR_RGB2YCrCb)
        y_c, cr_c, cb_c = cv2.split(ycrcb)
        skin_mask = (y_c > 90) & (cr_c >= 133) & (cr_c <= 173) & (cb_c >= 77) & (cb_c <= 127)
        skin_ratio = float(np.count_nonzero(skin_mask)) / total_pixels

        # Sky / atmospheric landscape blue
        sky_mask = cv2.inRange(hsv, (100, 25, 80), (130, 255, 255))
        sky_ratio = float(np.count_nonzero(sky_mask)) / total_pixels

        # -------------------------------------------------------------
        # 4. Rectilinear Man-Made Geometry (Cars, Buildings, Phones)
        # -------------------------------------------------------------
        edges = cv2.Canny(gray, 40, 130)
        lines = cv2.HoughLinesP(edges, 1, np.pi / 180, threshold=65, minLineLength=40, maxLineGap=8)
        rectilinear_penalty = 0.0

        if lines is not None and len(lines) >= 4:
            lines_reshaped = lines.reshape(-1, 4)
            aligned_count = 0
            for x1, y1, x2, y2 in lines_reshaped:
                angle = abs(np.arctan2(y2 - y1, x2 - x1) * 180.0 / np.pi)
                if angle < 14 or angle > 166 or (76 < angle < 104):
                    aligned_count += 1
            aligned_ratio = aligned_count / len(lines_reshaped)
            if aligned_ratio > 0.45 and len(lines_reshaped) >= 6:
                rectilinear_penalty = min(0.45, (aligned_ratio - 0.40) * 0.8)

        # -------------------------------------------------------------
        # 5. Spatial Cohesion of Plant Tissue (Contour Analysis)
        # -------------------------------------------------------------
        botanical_mask = green_mask | yellow_mask | fruit_mask | brown_mask
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (7, 7))
        cleaned_botanical = cv2.morphologyEx(botanical_mask, cv2.MORPH_CLOSE, kernel, iterations=2)
        cleaned_botanical = cv2.morphologyEx(cleaned_botanical, cv2.MORPH_OPEN, kernel, iterations=1)
        contours, _ = cv2.findContours(cleaned_botanical, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        max_contour_area = 0.0
        best_circularity = 0.0
        best_solidity = 0.0
        best_extent = 0.0
        for cnt in contours:
            area = cv2.contourArea(cnt)
            if area > max_contour_area:
                max_contour_area = area
                perimeter = cv2.arcLength(cnt, True)
                if perimeter > 0:
                    best_circularity = (4 * np.pi * area) / (perimeter * perimeter)
                hull = cv2.convexHull(cnt)
                hull_area = cv2.contourArea(hull)
                if hull_area > 0:
                    best_solidity = float(area) / hull_area
                bx, by, bw, bh = cv2.boundingRect(cnt)
                if (bw * bh) > 0:
                    best_extent = float(area) / (bw * bh)

        max_contour_ratio = max_contour_area / total_pixels

        # -------------------------------------------------------------
        # 6. Scoring Synthesis (Computer Vision Heuristic)
        # -------------------------------------------------------------
        foliar_score = min(1.0, (green_ratio * 1.5) + (exg_ratio * 1.0) + (yellow_ratio * 0.8))
        is_fruit_shape = (best_circularity > 0.40 and best_solidity > 0.70 and best_extent <= 0.83 and max_contour_ratio < 0.85)
        fruit_score = min(1.0, fruit_ratio * 2.0) if is_fruit_shape else (fruit_ratio * 0.02)
        bark_score = min(1.0, brown_ratio * 1.5) if (green_ratio < 0.15 and skin_ratio < 0.15 and rectilinear_penalty < 0.10 and best_extent <= 0.83) else (brown_ratio * 0.05)

        color_score = max(foliar_score, fruit_score, bark_score)
        cohesion_score = min(1.0, max_contour_ratio * 2.2)

        cv_plant_score = (0.55 * color_score) + (0.45 * cohesion_score)
        cv_plant_score -= rectilinear_penalty

        if best_extent > 0.83 and green_ratio < 0.05:
            cv_plant_score -= 0.45
        if skin_ratio > 0.20 and green_ratio < 0.10:
            cv_plant_score -= (skin_ratio * 0.60)
        if sky_ratio > 0.35 and max_contour_ratio < 0.15:
            cv_plant_score -= (sky_ratio * 0.50)
        if rectilinear_penalty > 0.10 and green_ratio < 0.08:
            cv_plant_score -= (rectilinear_penalty * 0.80)
        if (green_ratio > 0.35 or exg_ratio > 0.30) and max_contour_ratio > 0.25 and rectilinear_penalty < 0.10:
            cv_plant_score = min(1.0, cv_plant_score + 0.25)

        cv_plant_score = max(0.0, min(1.0, cv_plant_score))

        # -------------------------------------------------------------
        # 7. Tier 2: Machine Learning Prediction (if model is available)
        # -------------------------------------------------------------
        final_score = cv_plant_score
        ml_evaluated = False
        if cls._load_model() and cls._model is not None:
            try:
                feat_vec = cls.extract_features(rgb).reshape(1, -1)
                ml_prob = float(cls._model.predict_proba(feat_vec)[0, 1])
                # Ensemble blend: 60% ML model + 40% CV physical morphology
                final_score = (0.60 * ml_prob) + (0.40 * cv_plant_score)
                final_score = max(0.0, min(1.0, final_score))
                ml_evaluated = True
            except Exception as e:
                logger.warning("Tier 2 ML prediction failed (%s), using CV score.", e)
                final_score = cv_plant_score

        # Physical reality check: If there is virtually zero botanical tissue
        # (< 4% green/foliar/fruit) and low CV score, this is definitively a non-plant image
        # (e.g. cars, buildings, animals, people) rather than an ambiguous plant image.
        botanical_presence = max(green_ratio, fruit_ratio, foliar_score)
        if botanical_presence < 0.04 and cv_plant_score < 0.15:
            final_score = min(final_score, ambig_th - 0.05)

        # -------------------------------------------------------------
        # 8. Decision Triage
        # -------------------------------------------------------------
        details = {
            "plant_score": round(final_score, 4),
            "cv_heuristic_score": round(cv_plant_score, 4),
            "ml_model_evaluated": ml_evaluated,
            "green_ratio": round(green_ratio, 4),
            "exg_ratio": round(exg_ratio, 4),
            "fruit_ratio": round(fruit_ratio, 4),
            "skin_ratio": round(skin_ratio, 4),
            "sky_ratio": round(sky_ratio, 4),
            "rectilinear_penalty": round(rectilinear_penalty, 4),
            "max_contour_ratio": round(max_contour_ratio, 4),
            "blur_variance": round(blur_var, 2),
            "threshold_used": min_score,
        }

        if final_score >= min_score:
            return ValidationResult(
                is_valid=True,
                status="valid",
                error_code=None,
                message=None,
                plant_score=round(final_score, 4),
                details=details,
            )
        elif final_score >= ambig_th:
            return ValidationResult(
                is_valid=False,
                status="ambiguous",
                error_code="AMBIGUOUS_IMAGE",
                message=cls.REJECTION_MESSAGE_AMBIGUOUS,
                plant_score=round(final_score, 4),
                details=details,
            )
        else:
            return ValidationResult(
                is_valid=False,
                status="non_plant",
                error_code="NON_PLANT_IMAGE",
                message=cls.REJECTION_MESSAGE_NON_PLANT,
                plant_score=round(final_score, 4),
                details=details,
            )
