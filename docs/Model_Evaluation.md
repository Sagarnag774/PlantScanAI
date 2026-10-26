# PlantScan AI â€” Model Evaluation & Benchmark Report

**Evaluation Standards:** Phase 1 Project Report (MobileNetV2, >=85% Target, OOD Detection)
**Location:** `datasets/reports/model/`
**Weights:** `ml/weights/`

---

## 1. Summary of Evaluated Models

| Model Pipeline | Input Shape | Model Format | Test Accuracy | Macro F1 | Weighted F1 | 85% Target Status |
|---|---|---|---|---|---|---|
| **Stage 1 Plant-Part Classifier (Cleaned)** | `(224, 224, 3)` | TFLite (2.42 MB) | **93.94%** | **0.9372** | **0.9410** | **TARGET EXCEEDED** (Verified Photos Only) |
| **Stage 1 Plant-Part Classifier (Old Baseline)** | `(224, 224, 3)` | TFLite (2.42 MB) | *81.97%* | *0.8171* | *0.8155* | *Contaminated (Drawings/Patents/Dead Leaves)* |
| **Stage 2 Tomato Classifier** | `(224, 224, 3)` | TFLite (2.45 MB) | **84.88%** | **0.8410** | **0.8470** | Near Target (Gap: -0.12%) |
| **Stage 2 Grape Classifier** | `(224, 224, 3)` | TFLite (2.35 MB) | **78.57%** | **0.7812** | **0.7850** | Gap: -6.43% |
| **Stage 2 Maize Classifier** | `(224, 224, 3)` | TFLite (2.38 MB) | **70.27%** | **0.6980** | **0.7015** | Gap: -14.73% |
| **Stage 2 Rice Classifier** | `(224, 224, 3)` | TFLite (2.41 MB) | **69.21%** | **0.6875** | **0.6910** | Gap: -15.79% |
| **Stage 2 Apple Classifier** | `(224, 224, 3)` | TFLite (2.36 MB) | **64.29%** | **0.6390** | **0.6415** | Gap: -20.71% |
| **PlantVillage Benchmark (15-Class)** | `(224, 224, 3)` | TFLite (2.44 MB) | **48.33%** | **0.4369** | **0.4369** | Initial Baseline (3 Epochs Frozen) |
| **Out-of-Distribution (OOD) Detector** | Multi-source | Algorithm / $\tau=0.70$ | **AUROC: 0.9177** | **TNR: 91.43%** | **FPR: 8.57%** | **MET (Effective Safe Rejection)** |

---

## 2. Stage 1 MobileNetV2 Plant-Part Classifier: Cleaned vs. Contaminated Comparison

### 2.1 Comparative Performance Matrix

| Evaluation Dimension | Old Baseline (Contaminated) | Retrained Model (Cleaned & Verified) | Delta / Scientific Assessment |
|---|---|---|---|
| **Dataset Path** | `datasets/plant_parts/` (uncleaned) | `datasets/plant_parts_cleaned/` | Contaminated artifacts removed to quarantine |
| **Dataset Composition** | Included 52 illustrations/engravings, 7 patent pages, 43 mislabeled organs, 29 landscapes, 11 non-plant objects | 227 confirmed genuine botanical photographs only | 100% verified plant photography |
| **Test Accuracy** | **81.97%** (50 / 61 correct) | **93.94%** (31 / 33 correct) | **+11.97%** improvement |
| **Macro F1-Score** | 0.8171 | **0.9372** | **+0.1201** |
| **Weighted F1-Score** | 0.8155 | **0.9410** | **+0.1255** |
| **Bark F1-Score** | 0.8966 (P: 0.867, R: 0.929) | **0.9630** (P: 1.000, R: 0.929) | Bark texture highly distinctive |
| **Fruit F1-Score** | 0.7273 (P: 0.765, R: 0.692) | **1.0000** (P: 1.000, R: 1.000) | Limited test sample size ($N=2$) |
| **Leaf F1-Score** | 0.9091 (P: 0.857, R: 0.968) | **0.9286** (P: 0.929, R: 0.929) | High fidelity foliar discrimination |
| **Stem F1-Score** | 0.7353 (P: 0.750, R: 0.721) | **0.8571** (P: 0.750, R: 1.000) | 100% recall on genuine rice culms/sheaths |
| **Test Set Support** | $N=61$ (Contaminated) | $N=33$ (Untouched Cleaned) | Evaluated once on held-out test split |

### 2.2 Cleaned Test Set Confusion Matrix ($N=33$)
```
             Predicted
           Bark  Fruit  Leaf  Stem
True Bark   13     0      1     0    (Recall: 92.9%)
True Fruit   0     2      0     0    (Recall: 100.0%)
True Leaf    0     0     13     1    (Recall: 92.9%)
True Stem    0     0      0     3    (Recall: 100.0%)
```

### 2.3 Sample Scarcity & Honest Limitation Disclosure
While the retrained MobileNetV2 achieves **93.94% test accuracy** on verified photographs, an acute sample shortage persists in `Fruit` ($N_{\text{test}}=2$, $N_{\text{train}}=15$) and `Stem` ($N_{\text{test}}=3$, $N_{\text{train}}=24$) due to strict purging of non-photographic artifacts. While statistical precision is high, statistical power on these two classes is limited by small sample size. Therefore, Phase 1 benchmark sign-off requires expanding the photographic corpus to $\ge 50$ training images per class before declaring final production readiness.

---

## 3. Formal Out-of-Distribution (OOD) Evaluation

- **Evaluation Harness**: `ml/unknown_detector/ood_evaluator.py`
- **Report Location**: `datasets/reports/model/ood_evaluation_report.json`
- **Total Test Samples**: 170 (100 In-Distribution Tomato Leaf Test, 70 Out-of-Distribution Anomaly Samples)
- **AUROC**: **0.9177**
- **True Negative Rate (OOD Rejection Rate)**: **91.43%** (64 / 70 anomalies rejected)
- **False Positive Rate (OOD Acceptance Rate)**: **8.57%** (6 / 70 anomalies accepted)
- **FPR at 95% TPR (FPR95)**: **18.57%**

### Category-wise OOD Breakdown:
1. **Unsupported Bark (Woody periderm)**: 15/15 rejected (**100.0%**) via Stage 1 Anatomical Gate.
2. **Unsupported Stem**: 11/15 rejected (**73.3%**).
3. **Non-Plant Textures**: 8/10 rejected (**80.0%**).
4. **Featureless Low-Illumination**: 10/10 rejected (**100.0%**) via Vision Morphological Filter.
5. **High Entropy Noise**: 10/10 rejected (**100.0%**) via Softmax Entropy Spread.
6. **Severe Blur / Unfocused**: 10/10 rejected (**100.0%**).

---

## 4. Root Cause Analysis for Models Below 85% Target

1. **In-Field PlantDoc Real-World Noise**: Unlike clean laboratory PlantVillage images (solid neutral backgrounds, perfect illumination, excised flat leaves), the Indian agricultural multi-source dataset (Rice, Apple, Cotton, Banana, Mango) incorporates in-field PlantDoc photographs with harsh direct sunlight, deep shadows, complex soil backgrounds, and overlapping leaves.
2. **Multi-Label Lesions on Single Leaves**: In real agricultural fields, a single apple or rice leaf often exhibits both fungal leaf blast and bacterial blight concurrently, leading to lower single-label top-1 precision on the benchmark.
3. **Phase 3 Interventions Applied**:
   - Integrated `RandomRotation(0.15)`, `RandomBrightness(0.15)`, `RandomContrast(0.15)`, `RandomZoom(0.1)`, `RandomFlip('horizontal')`, and `GaussianNoise(0.03)` into `experiments/train_crop_mobilenetv2.py`.
   - Applied Stage 1 anatomical plant-part screening to prevent stem and bark samples from distorting foliar leaf training distributions.
