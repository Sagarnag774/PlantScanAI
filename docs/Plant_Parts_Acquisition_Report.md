# PlantScanAI: Phase 1 Real Plant-Part Dataset Acquisition & Staging Report

**Date:** October 26, 2026
**Auditor / ML Engineer:** Antigravity Pair-Programming Specialist
**Workspace:** `d:/Sagarnag/major project/pgpt/PlantScanAI`
**Branch:** `feature/phase-2-backend-docs`
**Compliance Standards:** PlantScanAI Phase 1 Specification & Quality Remediation Protocol

---

## 1. Executive Summary

To resolve the severe class imbalances and contamination from historical botanical sketches, scanned engravings, and mislabeled foliar debris identified during the dataset quality audit, an acquisition pipeline was designed and executed.

Prior to acquisition, the cleaned inventory stood at:
- **Bark:** 92 photos
- **Leaf:** 91 photos
- **Fruit:** 24 photos (76-photo deficit)
- **Stem:** 34 photos (66-photo deficit)
- **Total Cleaned Images:** 241

Through research-grade external queries to **iNaturalist Open Data** hosted on AWS, perceptual dHash screening, cryptographic duplicate prevention, automated image quality metrics, and visual human-in-the-loop curation across 342 downloaded candidates:
1. **159 genuine, verified photographs** were approved and staged across balanced `train`, `val`, and `test` splits.
2. **152 candidates** were formally rejected and quarantined with recorded defect rationales.
3. **The 100-image milestone per class was achieved**: Each of the 4 classes (`bark`, `fruit`, `leaf`, `stem`) now contains exactly **100 verified photographs** (70 train, 15 val, 15 test), totaling **400 balanced photographs**.
4. **The original dataset (`datasets/plant_parts/`, 397 files) remains strictly preserved and byte-for-byte untouched.**
5. **Zero cross-split cryptographic duplicate leakage** and **zero observation-level specimen leakage** were verified.

---

## 2. Dataset Inventory & Milestone Reconciliation

### Class Breakdown Across Cleaned and Staged Sets

| Class | Cleaned Photos (`plant_parts_cleaned`) | Staged Approved (`plant_parts_staging/approved`) | Combined Total | Target Milestone | Status |
| :--- | :---: | :---: | :---: | :---: | :--- |
| **Bark** | 92 | 8 | **100** | 100 | **Target Achieved** |
| **Fruit** | 24 | 76 | **100** | 100 | **Target Achieved** |
| **Leaf** | 91 | 9 | **100** | 100 | **Target Achieved** |
| **Stem** | 34 | 66 | **100** | 100 | **Target Achieved** |
| **TOTAL** | **241** | **159** | **400** | **400** | **Balanced 4-Class Dataset** |

---

### Detailed Split Distribution (Cleaned + Staged = Combined)

| Class | Split | Cleaned | Staged Approved | Combined Total | Split Target |
| :--- | :---: | :---: | :---: | :---: | :---: |
| **Bark** | `train` | 63 | 7 | **70** | 70 |
| | `val` | 14 | 1 | **15** | 15 |
| | `test` | 15 | 0 | **15** | 15 |
| | **Subtotal** | **92** | **8** | **100** | **100** |
| **Fruit** | `train` | 19 | 51 | **70** | 70 |
| | `val` | 2 | 13 | **15** | 15 |
| | `test` | 3 | 12 | **15** | 15 |
| | **Subtotal** | **24** | **76** | **100** | **100** |
| **Leaf** | `train` | 65 | 5 | **70** | 70 |
| | `val` | 11 | 4 | **15** | 15 |
| | `test` | 15 | 0 | **15** | 15 |
| | **Subtotal** | **91** | **9** | **100** | **100** |
| **Stem** | `train` | 24 | 46 | **70** | 70 |
| | `val` | 7 | 8 | **15** | 15 |
| | `test` | 3 | 12 | **15** | 15 |
| | **Subtotal** | **34** | **66** | **100** | **100** |
| **OVERALL** | **All Splits** | **241** | **159** | **400** | **400** |

---

## 3. Provenance, Licensing & Attribution

All newly acquired photographs originate from research-grade observations in **iNaturalist Open Data** hosted on AWS Open Data Registry.

### License Compliance Distribution

Every staged image was vetted against open license requirements before downloading:

| License | Count | Percentage | Attribution / Usage Requirements |
| :--- | :---: | :---: | :--- |
| **CC-BY** | 113 | 71.1% | Creative Commons Attribution 4.0 International; author attribution preserved. |
| **CC0** | 34 | 21.4% | Public Domain Dedication; no restrictions, attribution retained. |
| **CC-BY-SA** | 12 | 7.5% | Creative Commons Attribution-ShareAlike 4.0; viral share-alike terms respected. |
| **Total** | **159** | **100.0%** | **100% Verified Open Research Licenses** |

Full attribution recordsâ€”including `observation_id`, `photo_id`, `photo_url`, `observation_url`, `license`, `attribution`, `sha256`, and perceptual `dhash_hex`â€”are preserved in:
- `datasets/plant_parts_staging/manifests/approved_staging_manifest.json`
- `datasets/plant_parts_staging/manifests/approved_staging_manifest.csv`

---

## 4. Visual Verification & Quality Curation Protocol

A critical finding from initial candidate queries was that **naive keyword or taxon filtering is insufficient for plant-part machine learning**:
- Citizen-science queries for `stem` frequently returned flower blossoms (e.g., giant sunflower flower heads, yellow tomato blossoms, cactus blooms).
- Queries for `fruit` frequently returned the first photo of an observation, which was often a distant orchard tree canopy, seedling foliage, or even a human observer.
- Several queries returned mushrooms/toadstools, insects resting on rocks, or herbarium dried specimens taped to paper.

### Automated Heuristics & Screening
Each downloaded candidate passed automated pre-screening:
1. **Resolution:** Minimum $300 \times 300$ pixels (upscaling prohibited).
2. **Sharpness:** Laplacian variance $\ge 35.0$ to discard motion blur.
3. **Parchment Ratio:** Paper/drawing mask ratio $< 0.40$ combined with HSV saturation check to discard historical engravings and textbook scans.
4. **Duplicate Prevention:** Cryptographic SHA-256 matching and perceptual dHash Hamming distance $\le 2$ against the 241 cleaned photos to prevent duplicates.

### Human-in-the-Loop Visual Review Results

Across **342 downloaded candidates**:
- **190 approved** (of which 159 were staged to meet exact split requirements).
- **152 rejected and quarantined** to `datasets/plant_parts_staging/rejected/`.

#### Summary of Curation Verdicts by Class:
| Class | Total Candidates | Approved | Rejected | Rejection Reasons |
| :--- | :---: | :---: | :---: | :--- |
| **Bark** | 27 | 8 | 19 | Foliage/leaves in foreground, distant forest landscapes, urban window view, human selfie. |
| **Fruit** | 147 | 84 | 63 | Flowers/blossoms, foliage only, orchard ground litter, distant hillsides, eaten apple core. |
| **Leaf** | 28 | 10 | 18 | Whole tree canopies, flowers, fallen acorns on ground, distant shrubs. |
| **Stem** | 140 | 88 | 52 | Sunflower blooms, cactus flowers, mushrooms/fungi, insects on rock, herbarium paper. |
| **Total** | **342** | **190** | **152** | Full review manifest in `datasets/reports/plant_parts_staging_review.json`. |

---

## 5. Taxa and Environmental Diversity

The staged approved images introduce significant agricultural and ecological diversity:

### Fruit Diversity (76 staged approved)
- **Apples (*Malus domestica*):** 18 images (hanging fruit clusters, red/green ripe fruit on orchard branches).
- **Sweet Oranges (*Citrus sinensis*) & Lemons (*Citrus limon*):** 18 images (ripe yellow/orange citrus on tree branches).
- **Strawberries (*Fragaria*):** 8 images (ripe red berries on field plants with leaves).
- **Pumpkins / Squash (*Cucurbita*):** 7 images (mature gourds/melons on vine stems).
- **Tomatoes (*Solanum lycopersicum*):** 6 images (ripe red tomatoes on vine clusters).
- **Eggplants (*Solanum melongena*):** 6 images (purple aubergine fruit on field plants).
- **Sweet Peppers (*Capsicum annuum*):** 5 images (red/green bell peppers on plants).
- **Cucumbers (*Cucumis sativus*):** 5 images (green cucumbers hanging from trellises).
- **Grapes (*Vitis vinifera*):** 3 images (ripe dark and green grape clusters on vines).

### Stem Diversity (66 staged approved)
- **Sugarcane (*Saccharum officinarum*):** 16 images (thick jointed culms/stalks with clear nodes).
- **Horsetail (*Equisetum* & *Equisetum hyemale*):** 22 images (distinct ribbed jointed green stems).
- **Bamboo (*Bambusa* & *Phyllostachys*):** 22 images (prominent culm internodes, culm sheaths, and nodal rings).
- **Giant Reed (*Arundo donax*):** 2 images (stout cane stalks).
- **Asparagus (*Asparagus officinalis*):** 1 image (herbaceous main shoot axis).
- **Rhubarb (*Rheum*):** 1 image (thick herbaceous edible stalk).
- **Prickly Pear (*Opuntia*):** 2 images (spiny succulent cladodes).

### Bark Diversity (8 staged approved)
- **Silver Birch (*Betula pendula*):** Distinct white peeling bark.
- **Sycamore (*Platanus*):** Peeling mottled bark plates.
- **Eucalyptus (*Eucalyptus*):** Fibrous and smooth trunk bark.
- **Scots Pine (*Pinus sylvestris*):** Furrowed trunk bark plates.
- **Oak (*Quercus*):** Rough, deeply fissured mature trunk bark.

### Leaf Diversity (9 staged approved)
- **Mulberry (*Morus*):** Crisp foliar leaf blades with serrate margins.
- **Fig (*Ficus*):** Distinct lobed green leaves.
- **Maple (*Acer*):** Palmate leaf blades showing chlorotic and healthy venation.
- **Mango (*Mangifera indica*):** Lanceolate glossy leaves.

---

## 6. Anti-Leakage & Specimen Isolation Architecture

To ensure a defensible evaluation of the MobileNetV2 classifier:

1. **Strict Specimen Isolation (`observation_id` grouping):**
   - In iNaturalist, an observer may photograph the same plant from multiple angles.
   - The acquisition script enforces atomic allocation: all photos sharing an `observation_id` are placed in the same split.
   - Verification check: **0 observation IDs cross split boundaries.**

2. **Zero Cryptographic Duplicate Leakage:**
   - Evaluated SHA-256 collision checks across all splits.
   - Verification check:
     - `Train` $\cap$ `Val`: **0 duplicates**
     - `Train` $\cap$ `Test`: **0 duplicates**
     - `Val` $\cap$ `Test`: **0 duplicates**
     - Staged $\cap$ Cleaned: **0 duplicates**

3. **Untouched Test Split:**
   - The test set contains **15 realistic photographs per class (60 total test images)**.
   - No models have been tuned or evaluated against this staged test set yet.

---

## 7. Exact Reproduction Commands

The entire acquisition, curation, and staging workflow is 100% reproducible:

```powershell
# 1. Query external candidates from iNaturalist Open Data
python datasets/scripts/acquire_plant_parts.py --query

# 2. Generate visual contact sheets for inspection
python datasets/scripts/acquire_plant_parts.py --review

# 3. Apply curation review decisions and allocate to staging splits
python datasets/scripts/acquire_plant_parts.py --stage

# 4. Verify integrity, file counts, and anti-leakage isolation
python scratch/verify_staged_dataset.py

# 5. Run automated unit test suite
python -m pytest ml/plant_part_classifier/test_plant_parts_audit.py -v
python -m pytest backend/tests/test_predict.py -v
```

---

## 8. Conclusion and Next Steps

- **Milestone Completed:** The plant-part dataset now possesses 100 verified photographs per class across balanced train (70), validation (15), and test (15) splits.
- **Model Training Notice:** In accordance with instructions, **the final model has not been retrained yet**. The newly staged dataset sits cleanly in `datasets/plant_parts_staging/approved/` ready for human verification before acceptance into the production pipeline.
- **Preservation Notice:** The original `datasets/plant_parts/` (397 images) and existing cleaned `datasets/plant_parts_cleaned/` (241 images) remain completely untouched and intact.
