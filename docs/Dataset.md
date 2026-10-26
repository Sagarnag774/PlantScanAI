# PlantScan AI — Dataset Architecture & Data Engineering Guide

**Version:** 1.0.0
**Target Domain:** Multilingual Mobile & Cloud Plant Pathology
**Dataset Root:** `datasets/`

---

## 1. Overview & Dataset Taxonomy

PlantScan AI operates a distributed multi-crop diagnostic pipeline covering **10 major commercial crops** and **46 canonical disease and healthy classes**. The dataset combines standardized benchmark plant pathology corpora (PlantVillage, PlantDoc, Paddy Doctor, Mendeley Data collections) curated for both controlled laboratory and in-field natural lighting conditions.

### Supported Crops & Canonical Class Taxonomy

| # | Crop Species | Scientific Name | Classes Count | Canonical Disease & Healthy Classes |
|---|---|---|---|---|
| 1 | **Tomato** | *Solanum lycopersicum* | 10 | `tomato_bacterial_spot`, `tomato_early_blight`, `tomato_late_blight`, `tomato_leaf_mold`, `tomato_septoria_leaf_spot`, `tomato_spider_mites`, `tomato_target_spot`, `tomato_yellow_leaf_curl_virus`, `tomato_mosaic_virus`, `tomato_healthy` |
| 2 | **Banana** | *Musa acuminata* | 4 | `banana_cordana`, `banana_pestalotiopsis`, `banana_sigatoka`, `banana_healthy` |
| 3 | **Cotton** | *Gossypium hirsutum* | 4 | `cotton_bacterial_blight`, `cotton_curl_virus`, `cotton_fusarium_wilt`, `cotton_healthy` |
| 4 | **Mango** | *Mangifera indica* | 8 | `anthracnose`, `bacterial_canker`, `cutting_weevil`, `die_back`, `gall_midge`, `powdery_mildew`, `sooty_mould`, `mango_healthy` |
| 5 | **Rice** | *Oryza sativa* | 6 | `bacterial_leaf_blight`, `brown_spot`, `leaf_blast`, `leaf_scald`, `sheath_blight`, `healthy_rice_leaf` |
| 6 | **Potato** | *Solanum tuberosum* | 3 | `potato_early_blight`, `potato_late_blight`, `potato_healthy` |
| 7 | **Bell Pepper** | *Capsicum annuum* | 3 | `bell_pepper_bacterial_spot`, `bell_pepper_cercospora_leaf_spot`, `bell_pepper_healthy` |
| 8 | **Maize** | *Zea mays* | 3 | `maize_gray_leaf_spot`, `maize_common_rust`, `maize_northern_leaf_blight` |
| 9 | **Apple** | *Malus domestica* | 3 | `apple_scab`, `apple_cedar_rust`, `apple_healthy` |
| 10 | **Grape** | *Vitis vinifera* | 2 | `grape_black_rot`, `grape_healthy` |

---

## 2. Primary Data Sources & Provenance

To achieve high generalization accuracy under realistic field photography (uncontrolled lighting, complex soil backgrounds, varied leaf angles), PlantScan AI draws from multiple authoritative repositories:

1. **PlantVillage (Penn State / EPFL)**:
   - Laboratory-controlled leaf captures against uniform backgrounds.
   - High label fidelity for Tomato, Potato, and Bell Pepper.
2. **PlantDoc (IIT Delhi)**:
   - In-field smartphone captures in Indian agricultural environments.
   - Crucial natural noise source for Apple, Grape, Maize, and Tomato.
3. **Mendeley Data — Bangladesh Mango Leaf Corpus**:
   - 8-class specialized mango foliar pest and disease dataset collected from Rajshahi and Chapainawabganj orchards.
4. **Mendeley Data — Cotton Leaf Collection & ICAR-CICR**:
   - Field symptoms of Leaf Curl Virus (*CLCuD*), Bacterial Blight (*Xanthomonas malvacearum*), and Fusarium Wilt.
5. **Mendeley Data — Banana Leaf Disease Corpus**:
   - Clear diagnostic images of Sigatoka (*Mycosphaerella musicola*), Cordana leaf spot, and Pestalotiopsis.
6. **Paddy Doctor & Rice Disease Benchmark (ICAR-NRRI)**:
   - Field pathology captures of major Asian rice leaf blights and blasts.

---

## 3. Storage & Directory Hierarchy

The repository maintains strict tiering between raw source archives, cleaned datasets, and model-ready train/val/test splits:

```
PlantScanAI/
└── datasets/
    ├── raw/                                # Downloaded source archives (unmodified)
    │   ├── PlantVillage/                   # Tomato, Potato, Bell Pepper
    │   ├── PlantDoc/                       # In-the-wild captures
    │   ├── Mango/                          # Mango leaf 8 classes
    │   ├── Banana/                         # Banana leaf 4 classes
    │   ├── Cotton/                         # Cotton leaf 4 classes
    │   └── Rice/                           # Rice leaf 6 classes
    │
    ├── processed/
    │   └── cleaned_raw/                    # Automated audit pass: corrupted, duplicates,
    │       ├── Apple/                      # and non-image files removed
    │       ├── Banana/
    │       └── ...
    │
    ├── model/                              # Model-ready stratified splits (224x224 px)
    │   ├── apple/
    │   │   ├── train/                      # 70% of cleaned dataset
    │   │   ├── val/                        # 15% of cleaned dataset
    │   │   └── test/                       # 15% holdout test set
    │   ├── grape/
    │   ├── tomato/
    │   └── ... [all 10 crops]
    │
    └── reports/
        └── model/                          # Persisted evaluation metrics per crop
            ├── apple/evaluation_report.json
            ├── grape/evaluation_report.json
            └── tomato/evaluation_report.json
```

---

## 4. Data Preparation & Split Strategy

### 4.1 Stratified Splitting
All crop datasets are split using stratified sampling to maintain class proportions across partitions:
- **Training Set (70%)**: Used for gradient backpropagation and feature extraction.
- **Validation Set (15%)**: Evaluated at each epoch for early stopping, model checkpointing, and learning rate scheduling.
- **Holdout Test Set (15%)**: Kept strictly untouched during model training; used exclusively for generating final classification reports, confusion matrices, and F1 benchmarks.

### 4.2 Data Cleansing Pipeline
Before splitting, all raw images pass through `datasets/scripts/audit_and_clean.py`:
1. **Integrity Validation**: Verifies JPEG/PNG/WebP headers using Pillow; truncations or CRC errors are purged.
2. **Dimension Filtering**: Images smaller than 32x32 pixels are discarded.
3. **Perceptual Hash Deduplication**: Exact and near-duplicate images across downloads are identified via MD5 and perceptual hashing (`imagehash.phash`), ensuring no data leakage across splits.
4. **Channel Canonicalization**: Images are converted to standard 3-channel RGB (converting Grayscale and stripping RGBA alpha channels).

---

## 5. Augmentation & Preprocessing Pipeline

### 5.1 Input Preprocessing
- **Resolution**: All images are resized to **224 × 224 pixels** using bilinear interpolation with antialiasing.
- **Channel Scaling**: Pixel values in $[0, 255]$ are scaled to $[-1, 1]$ matching the pre-trained MobileNetV2 ImageNet weights:
  $$x_{\text{norm}} = \frac{x}{127.5} - 1.0$$

### 5.2 On-The-Fly Training Augmentations
To prevent overfitting on laboratory backgrounds and simulate harsh outdoor field conditions, the training pipeline applies:
- **Random Horizontal & Vertical Flips** ($p=0.5$)
- **Random Rotation** (up to $\pm 25^\circ$)
- **Random Zoom** ($[0.85, 1.15]$)
- **Random Brightness & Contrast Modulation** ($\pm 15\%$)
- **Random Crop & Rescale** to simulate variable camera distances

Validation and test sets receive **zero stochastic augmentation**, undergoing only deterministic resize and normalization.

---

## 6. Class Imbalance Mitigation

Certain field classes (e.g., *Grape Black Rot* or *Rice Sheath Blight*) have fewer natural captures than standard laboratory classes (e.g., *Tomato Early Blight*). To ensure balanced recall:
1. **Balanced Batch Sampling / Class Weights**:
   $$w_c = \frac{N}{K \cdot N_c}$$
   Where $N$ is total samples, $K$ is number of classes, and $N_c$ is sample count for class $c$.
2. **Selective Offline Augmentation**: Synthetic perturbations are pre-generated for severely under-represented minority classes until reaching a minimum threshold of 100 images per class.

---

## 7. Stage 1 Plant-Parts Anatomical Dataset & Quality Audit

To fulfill the Phase 1 Report two-stage architectural mandate, a dedicated anatomical part dataset is maintained covering four botanical organs: `Leaf`, `Fruit`, `Stem`, and `Bark`.

### 7.1 Dataset Quality Audit & Defect Findings
An exhaustive quality audit of the initial 397-image dataset (`datasets/plant_parts/`) was conducted using automated quantitative screening combined with systematic human visual inspection across 12 generated contact sheets.

The audit revealed that open-access botanical queries from Wikimedia Commons and agricultural collections contained significant non-photographic and unsuitable artifacts:
1. **Botanical Drawings & Engravings (52 images)**: 19th-century lithographs ("The Delaware Grape"), seed catalog woodcuts ("5 Grand Tomatoes", "The Matchless Tomato"), and anatomical cross-section sketches.
2. **Scanned Documents & Patent Text Pages (7 images)**: Scanned United States Patent specifications (e.g., Wilmann 1896 Corn Husker claims) and seed catalog advertising text columns.
3. **Mislabeled Organs (43 images)**:
   - 34 curled, dead necrotic mango leaf blades from `datasets/raw/Mango/Die Back` inappropriately ingested as "stems".
   - Whole red apple fruit and Alamy apple scab fruits mislabeled as "leaves".
   - Sunflower and Gerbera flower blossoms mislabeled as "stems".
   - Bare dormant sapling twigs with label cards mislabeled as "fruit".
4. **Distant Landscapes Without Discernible Organ (29 images)**: Winter woodland vistas, distant bare dormant trees, and pastoral sheep fields without close-up organ depictions.
5. **Non-Plant Objects & Prepared Foods (11 images)**: Restaurant food plates (bruschetta bread with tomato topping), an ancient bronze coin depicting Pegasus, a steam tractor engine engraving, and military digital camouflage fabric pattern.

### 7.2 Strict Data Preservation & Reversible Segregation
To ensure zero data loss, the original dataset is strictly preserved without deletions, relabeling, or moves:
- **Pristine Original Archive**: `datasets/plant_parts/` (all 397 original files remain untouched).
- **Cleaned Dataset**: `datasets/plant_parts_cleaned/` (contains only the 227 confirmed genuine photographs).
- **Quarantine Storage**: `datasets/plant_parts_quarantine/` (contains all 170 rejected and manual-review items alongside `quarantine_manifest.json` documenting the exact reason for every quarantined file).
- **Reversal Procedure**: Cleanup can be reversed at any time via:
  ```bash
  python datasets/scripts/audit_plant_parts_dataset.py --reverse
  ```

### 7.3 Before-and-After Split & Class Distribution

| Split | Anatomical Class | Original (Before) | Retained Photographs (`keep`) | Quarantined Unsuitable (`reject`) | Awaiting Manual Review | Final Cleaned Count |
|---|---|---|---|---|---|---|
| **Train** | **Bark** | 70 | 63 | 4 | 3 | **63** |
| **Train** | **Fruit** | 70 | 15 | 49 | 6 | **15** |
| **Train** | **Leaf** | 70 | 58 | 1 | 11 | **58** |
| **Train** | **Stem** | 67 | 24 | 42 | 1 | **24** |
| **Val** | **Bark** | 15 | 14 | 1 | 0 | **14** |
| **Val** | **Fruit** | 15 | 2 | 13 | 0 | **2** |
| **Val** | **Leaf** | 15 | 11 | 2 | 2 | **11** |
| **Val** | **Stem** | 14 | 7 | 7 | 0 | **7** |
| **Test** | **Bark** | 15 | 14 | 0 | 1 | **14** |
| **Test** | **Fruit** | 15 | 2 | 11 | 2 | **2** |
| **Test** | **Leaf** | 15 | 14 | 0 | 1 | **14** |
| **Test** | **Stem** | 16 | 3 | 12 | 1 | **3** |
| **TOTAL** | — | **397** | **227 (57.2%)** | **142 (35.8%)** | **28 (7.1%)** | **227** |

### 7.4 Cryptographic Leakage & Deduplication Results
- **Cryptographic SHA-256 Duplicates**: 0 duplicate groups across the dataset.
- **Cross-Split Duplicate Leakage**: Exactly 0.0% leakage between train, val, and test splits.
- **Near-Duplicate Perceptual Hash (dHash)**: Exactly 1 pair identified within training split; 0 cross-split near-duplicate leakage.

### 7.5 Audit & Cleanup Tooling
The automated screening, contact sheet generation, and segregation pipeline is executed via:
```bash
# 1. Run audit, generate contact sheets, and export inventory & audit reports:
python datasets/scripts/audit_plant_parts_dataset.py --audit --contact-sheets

# 2. Build segregated cleaned dataset and quarantine directory:
python datasets/scripts/audit_plant_parts_dataset.py --clean

# 3. Run regression and verification test suite:
pytest ml/plant_part_classifier/test_plant_parts_audit.py -v
```

Generated reports:
- Inventory: `datasets/reports/plant_parts_inventory.json` & `.csv`
- Audit Decisions: `datasets/reports/plant_parts_audit_report.json` & `.csv`
- Visual Contact Sheets: `datasets/reports/contact_sheets/contact_sheet_{split}_{class}.jpg` (12 sheets)
- Quarantine Manifest: `datasets/plant_parts_quarantine/quarantine_manifest.json`

### 7.6 Class Balance Findings & Readiness for Model Training
1. **Bark & Leaf Readiness**: `Bark` (91 confirmed photos) and `Leaf` (83 confirmed photos) possess clean, high-resolution photographic representations across all partitions with rich natural texture and realistic field variations.
2. **Fruit & Stem Shortage**: Purging non-photographic illustrations and mislabeled dried foliage left an acute sample shortage in `Fruit` (19 photos: 15 train, 2 val, 2 test) and `Stem` (34 photos: 24 train, 7 val, 3 test).
3. **Training Recommendation**: While `datasets/plant_parts_cleaned/` is verified free of illustrations, sketches, and non-plant artifacts, **it is NOT recommended to train the final production MobileNetV2 model until `Fruit` and `Stem` classes are supplemented** with at least 50 additional genuine photographs each (sourced from local field captures or verified agricultural repositories like PlantDoc/PaddyDoctor). Training on 15 fruit and 24 stem images would result in severe class imbalance and poor validation generalization.

---

## 8. PlantVillage 38-Class Benchmark Dataset

Per the Phase 1 Project Report (Mohanty et al., 2016), the standard benchmark comprises **38 disease and healthy classes across 14 crop species**:

- **Preparation Script**: `datasets/scripts/prepare_plantvillage_38_benchmark.py`
- **Output Directory**: `datasets/plantvillage_38/{train,validation,test}`
- **Benchmark Report**: `datasets/reports/plantvillage_38_dataset_report.json`
- **Status Breakdown**:
  - **15 Classes Verified Locally**: Pepper (2), Potato (3), Tomato (10) sourced from verified PlantVillage archives.
  - **23 Classes Cataloged for Ingestion**: Apple (4), Blueberry (1), Cherry (2), Corn (4), Grape (4), Orange (1), Peach (2), Raspberry (1), Soybean (1), Squash (1), Strawberry (2).
  - Automated download harness connects directly to the official upstream repository (`https://github.com/spMohanty/PlantVillage-Dataset`).
