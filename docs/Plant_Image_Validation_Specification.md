# PlantScanAI: Stage 0 Non-Plant Image Detection & Rejection Architecture

## 1. Executive Summary & Objective

In real-world agricultural deployments, users frequently upload out-of-scope images—such as people, automobiles, buildings, domestic animals, food, smartphones, or general landscapes lacking visible vegetation. Standard closed-world deep learning disease classifiers, when presented with such out-of-distribution inputs, erroneously assign a high-confidence plant disease (e.g., classifying a red car as *Tomato Late Blight* or a brick building as *Cedar Apple Rust*).

To eliminate this fundamental computer vision failure mode, **PlantScanAI** integrates **Stage 0: Plant-Image Presence Validation**. When an uploaded image does not contain a supported plant or botanical tissue, the system immediately rejects the image before any disease classification model is invoked, returning HTTP 422:

```json
{
  "success": false,
  "error_code": "NON_PLANT_IMAGE",
  "message": "The uploaded image does not appear to contain a plant. Please upload a clear image of a plant leaf or another supported plant part.",
  "prediction": null
}
```

The underlying disease inference engine (`engine.predict`) is **never executed** on rejected inputs, guaranteeing that non-plant imagery can never trigger false disease diagnoses or improper chemical pesticide recommendations.

---

## 2. Validation Architecture & Two-Tier Pipeline

PlantScanAI implements a two-tier hybrid architecture combining deterministic computer vision colorimetry and morphological physics with a trained 51-dimensional ensemble machine learning classifier.

```
Uploaded Image (JPEG / PNG / WebP)
              │
              ▼
[Image Processor: Decode & Sanitize]
  ├─ Corrupted File / Bad Stream ──► HTTP 400 Bad Request
  └─ Decoded (H, W, 3) RGB Array
              │
              ▼
[Stage 0: PlantImageValidator.validate()]
  ├─ Blur & Focus Check (Laplacian Variance < 20.0) ──► HTTP 422 (BLURRY_IMAGE)
  ├─ Contrast & Degeneracy (Std Dev < 5.0) ───────────► HTTP 422 (LOW_QUALITY_IMAGE)
  │
  ├─ Tier 1: Deterministic Physics & Morphology Engine
  │    ├─ Excess Green (ExG), Excess Red (ExR), Excess Blue (ExB) Indices
  │    ├─ HSV & LAB Chlorophyll Foliar Bounds
  │    ├─ Anthropogenic Rectilinear Edge Geometry (Sobel / Hough Lines)
  │    ├─ YCrCb Human Skin Tone Filter
  │    ├─ Atmospheric Sky Blue Dispersion
  │    └─ Contour Cohesion, Circularity, Solidity & Bounding-Box Extent
  │
  ├─ Tier 2: 51-D Feature Extraction & ExtraTreesClassifier
  │    └─ Calibrated Ensemble Probability Score: P(Plant) ∈ [0.0, 1.0]
  │
  ▼
[Decision Triage]
  ├─ Score >= 0.50 ─────────────────► ACCEPT: Proceed to Stage 1 Crop Routing & Disease Inference
  ├─ 0.35 <= Score < 0.50 ──────────► UNCERTAIN: HTTP 422 (AMBIGUOUS_IMAGE - Request Clearer Photo)
  └─ Score < 0.35 or No Plant Tissue ► REJECT: HTTP 422 (NON_PLANT_IMAGE)
```

### Tier 1: Physics & Colorimetry Engine
1. **Vegetation Indices**:
   - Normalized Green Ratio: $G / (R + G + B + \epsilon)$
   - Excess Green Index (ExG): $2G - R - B$
   - Excess Red Index (ExR): $1.4R - G$
   - Excess Blue Index (ExB): $1.4B - G$
2. **Color Space Boundaries**:
   - Chlorophyll foliar tissue: $H \in [25^\circ, 95^\circ]$, $S \ge 35$, $V \ge 35$
   - Chlorotic/yellow tissue: $H \in [18^\circ, 35^\circ]$, $S \ge 40$, $V \ge 40$
   - Botanical fruits (tomato, apple, grape): red hue wrap $H < 12^\circ$ or $H > 165^\circ$, circularity $> 0.40$, bounding-box extent $\le 0.83$ (distinguishing spherical fruits from rectangular red brick masonry).
3. **Non-Plant Rejection Filters**:
   - Rectilinear Structural Penalty: Sobel gradient angle alignment along orthogonal axes ($0^\circ, 90^\circ, 180^\circ$) and Hough line segments detecting anthropogenic structures (cars, buildings, electronics).
   - Human Skin Tone Filter: YCrCb color space bounds ($Cr \in [133, 173]$, $Cb \in [77, 127]$).
   - Atmospheric Sky Filter: Sky blue bounds ($H \in [100^\circ, 130^\circ]$, $S \in [30, 180]$, $V > 100$).

### Tier 2: 51-Dimensional Machine Learning Classifier
- **Features Extracted**: 51 comprehensive statistical features across RGB, HSV, LAB, Sobel gradients, vegetation index distributions, and contour spatial morphology.
- **Model Architecture**: Ensemble ExtraTreesClassifier (100 estimators, entropy criterion) trained on real agricultural specimens and diverse negative images.
- **Artifact**: Lightweight Joblib model saved at `ml/weights/plant_validator/plant_validator_model.joblib` (< 1.2 MB).

---

## 3. Dataset & Empirical Evaluation

The validation model was trained and evaluated on a benchmark dataset comprising real agricultural field imagery and diverse out-of-distribution non-plant photographs.

### Dataset Distribution
| Category | Samples | Source / Composition |
| :--- | :--- | :--- |
| **Plant Specimens (Positive)** | 393 | High-resolution field photos across all 10 supported crops (Tomato, Potato, Corn, Apple, Grape, Rice, Wheat, Cotton, Sugarcane, Mango) covering healthy leaves, foliar lesions, and supported fruits. |
| **Non-Plant: Automobiles** | 40 | Cars, trucks, wheels, tires, asphalt, dashboards, metallic panels. |
| **Non-Plant: Architecture** | 40 | Brick walls, concrete buildings, windows, doors, interior rooms. |
| **Non-Plant: Humans / People** | 40 | Facial portraits, skin textures, hands, casual selfies. |
| **Non-Plant: Animals** | 40 | Domestic dogs, cats, cows, horses, birds. |
| **Non-Plant: Food & Cooked Dishes** | 40 | Cooked meals, pizzas, bread, soups, plated dining. |
| **Non-Plant: Electronics & Objects** | 40 | Smartphones, laptops, keyboards, desk accessories. |
| **Non-Plant: Scenery & Sky** | 40 | Open sky landscapes, clouds, open sea, deserts without visible plants. |
| **Total Benchmark Dataset** | **673** | **393 Positive (58.4%) / 280 Negative (41.6%)** |

### Evaluation Metrics (Audit Report: `datasets/reports/model/plant_validation_report.json`)
- **Overall Test Accuracy**: **99.41%**
- **AUROC (Area Under ROC Curve)**: **1.0000**
- **Plant Acceptance Rate (TPR)**: **98.99%**
- **Plant False Rejection Rate (FNR)**: **1.01%**
- **Non-Plant Rejection Rate (TNR)**: **100.00%**
- **Non-Plant False Acceptance Rate (FPR)**: **0.00%**

---

## 4. API Endpoints & Response Schema

### Endpoints
- `POST /api/v1/predict` (Multipart file upload)
- `POST /api/v1/predict/json` (Base64 JSON payload)

### Rejection Response (HTTP 422 Unprocessable Content)
```json
{
  "success": false,
  "status": "invalid_image",
  "error_code": "NON_PLANT_IMAGE",
  "message": "The uploaded image does not appear to contain a plant. Please upload a clear image of a plant leaf or another supported plant part.",
  "hint": "Please upload a clear image of a plant leaf or another supported plant part.",
  "prediction": null,
  "details": {
    "plant_score": 0.30,
    "cv_heuristic_score": 0.0,
    "ml_model_evaluated": true,
    "green_ratio": 0.0013,
    "exg_ratio": 0.0010,
    "fruit_ratio": 0.0001,
    "skin_ratio": 0.0,
    "sky_ratio": 0.2063,
    "rectilinear_penalty": 0.45,
    "max_contour_ratio": 0.0012,
    "blur_variance": 688.62,
    "threshold_used": 0.50
  }
}
```

### Ambiguous Image Response (HTTP 422 Unprocessable Content)
```json
{
  "success": false,
  "status": "invalid_image",
  "error_code": "AMBIGUOUS_IMAGE",
  "message": "The presence of a plant or supported plant part cannot be reliably determined. Please upload a closer, clearer photo of the plant leaf or fruit.",
  "hint": "Please upload a clear image of a plant leaf or another supported plant part.",
  "prediction": null
}
```

### Blurry Image Response (HTTP 422 Unprocessable Content)
```json
{
  "success": false,
  "status": "invalid_image",
  "error_code": "BLURRY_IMAGE",
  "message": "The uploaded image is too blurry to reliably detect plant features. Please hold your camera steady and upload a sharp, well-focused photo.",
  "hint": "Please upload a clear image of a plant leaf or another supported plant part.",
  "prediction": null
}
```

### Corrupted File Response (HTTP 400 Bad Request)
```json
{
  "status": "invalid_image",
  "error_code": "UNIDENTIFIED_IMAGE",
  "message": "The uploaded file is not a recognized image or is severely corrupted.",
  "hint": "Ensure you are uploading a valid JPEG, PNG, BMP, or WebP image."
}
```

---

## 5. Configuration Options

Configured in `backend/config.py` and overrideable via environment variables:

| Variable | Type | Default | Description |
| :--- | :--- | :--- | :--- |
| `PLANT_VALIDATION_ENABLED` | bool | `True` | Master kill-switch to enable/disable Stage 0 validation. |
| `PLANT_VALIDATION_THRESHOLD` | float | `0.50` | Minimum ensemble probability to accept an image as a valid plant. |
| `PLANT_AMBIGUOUS_THRESHOLD` | float | `0.35` | Lower threshold for ambiguity band ($[0.35, 0.50)$). |
| `BLUR_THRESHOLD` | float | `20.0` | Minimum Laplacian focus variance required. |

---

## 6. Frontend Behavior & User Interface

The diagnostic studio (`backend/static/scan.html`, `js/scan.js`, `css/styles.css`) dynamically presents validation outcomes:

1. **Submission Preview Retained**: The left-hand preview container (`#previewContainer`) remains visible so the user can verify the exact file submitted.
2. **Rejection Banner Displayed**:
   - The results placeholder (`#resultsPlaceholder`) and diagnosis container (`#resultsContent`) are hidden.
   - The rejection panel (`#rejectionPanel`) is activated with appropriate visual accenting:
     - Crimson theme (`🚫 VALIDATION REJECTED`) for non-plant uploads.
     - Amber theme (`⚠️ AMBIGUOUS IMAGE` / `🔍 BLURRY IMAGE`) for borderline or out-of-focus submissions.
3. **Suppression of Disease Attributes**:
   - No disease name or canonical label is rendered.
   - No confidence percentage or Plant Health Score gauge is rendered.
   - No IPM pesticide or organic treatment tabs are generated.
4. **Seamless Re-Upload Workflow**:
   - An interactive button (`Upload Another Plant Photo`) immediately clears the state and triggers the native file selector without requiring a browser refresh.

---

## 7. How to Run the Automated Tests & Verification

### Run the Full Backend Test Suite
```bash
python -m pytest backend/tests -v
```
*Current result: 52/52 tests passing (100%).*

### Run the Dedicated Plant Validation Test Suite
```bash
python -m pytest backend/tests/test_plant_validation.py -v
```
Covers:
1. Valid plant leaf acceptance.
2. Person photo rejection.
3. Animal photo rejection.
4. Car photo rejection.
5. Building photo rejection.
6. Landscape photo rejection.
7. Blurry photo rejection.
8. Corrupted stream rejection.
9. Unsupported file extension rejection.
10. Ambiguous borderline image clarification.
11. Architectural proof that `engine.predict()` is never called on rejected images.
12. Base64 JSON rejection endpoint.

### Run End-to-End Section 12 Verification Script
```bash
python scripts/verify_cases.py
```
*Verifies Case A (Car), Case B (Tomato leaf), Case C (Blurry image), and Case D (Corrupted stream).*

---

## 8. Known Limitations & Edge Cases

1. **Dried/Herbarium Specimens**: Completely desiccated or brown pressed leaves with no chlorophyll may receive lower color scores; the morphology engine compensates using leaf contours, but extreme dry samples may fall into the ambiguous range.
2. **Extreme Close-Up Macro Textures**: Macro photographs zoomed in to a microscopic fraction of a millimeter without leaf contour edges rely purely on cellular texture rather than whole-leaf geometry.
3. **Silkscreen Plant Illustrations / Toys**: Artificial plastic plants or printed t-shirts featuring realistic botanical drawings may trigger green vegetation indices; the rectilinear and high-frequency edge analysis mitigates synthetic prints.
