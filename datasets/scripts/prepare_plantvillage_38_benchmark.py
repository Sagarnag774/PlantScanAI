"""
PlantScanAI - PlantVillage 38-Class Benchmark Dataset Preparation & Audit Pipeline
Authoritative Benchmark per Phase 1 Project Report (Mohanty et al., 2016)

Covers 38 disease/healthy classes across 14 crop species:
1. Apple (4 classes)
2. Blueberry (1 class)
3. Cherry (2 classes)
4. Corn (maize) (4 classes)
5. Grape (4 classes)
6. Orange (1 class)
7. Peach (2 classes)
8. Pepper, bell (2 classes)
9. Potato (3 classes)
10. Raspberry (1 class)
11. Soybean (1 class)
12. Squash (1 class)
13. Strawberry (2 classes)
14. Tomato (10 classes)

Features:
- Cryptographic SHA-256 duplicate detection preventing partition leakage
- Stratified 70/15/15 train/val/test split
- Integration with local verified PlantVillage raw images
- Automated fetching for missing benchmark classes from official PlantVillage repository
- Manifest generation at datasets/reports/plantvillage_38_dataset_report.json
"""

import argparse
import hashlib
import json
import os
import random
import shutil
import sys
import time
import urllib.request
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple
from PIL import Image

PROJECT_ROOT = Path(__file__).resolve().parents[2]
RAW_PLANTVILLAGE_DIR = PROJECT_ROOT / "datasets" / "raw" / "PlantVillage"
BENCHMARK_OUTPUT_DIR = PROJECT_ROOT / "datasets" / "plantvillage_38"
REPORT_OUTPUT_PATH = PROJECT_ROOT / "datasets" / "reports" / "plantvillage_38_dataset_report.json"

# Authoritative 38-class taxonomy across 14 crop species
PLANTVILLAGE_38_CLASSES = [
    # 1. Apple (4)
    "Apple___Apple_scab",
    "Apple___Black_rot",
    "Apple___Cedar_apple_rust",
    "Apple___healthy",
    # 2. Blueberry (1)
    "Blueberry___healthy",
    # 3. Cherry (2)
    "Cherry_(including_sour)___Powdery_mildew",
    "Cherry_(including_sour)___healthy",
    # 4. Corn / Maize (4)
    "Corn_(maize)___Cercospora_leaf_spot Gray_leaf_spot",
    "Corn_(maize)___Common_rust_",
    "Corn_(maize)___Northern_Leaf_Blight",
    "Corn_(maize)___healthy",
    # 5. Grape (4)
    "Grape___Black_rot",
    "Grape___Esca_(Black_Measles)",
    "Grape___Leaf_blight_(Isariopsis_Leaf_Spot)",
    "Grape___healthy",
    # 6. Orange (1)
    "Orange___Haunglongbing_(Citrus_greening)",
    # 7. Peach (2)
    "Peach___Bacterial_spot",
    "Peach___healthy",
    # 8. Pepper, bell (2)
    "Pepper,_bell___Bacterial_spot",
    "Pepper,_bell___healthy",
    # 9. Potato (3)
    "Potato___Early_blight",
    "Potato___Late_blight",
    "Potato___healthy",
    # 10. Raspberry (1)
    "Raspberry___healthy",
    # 11. Soybean (1)
    "Soybean___healthy",
    # 12. Squash (1)
    "Squash___Powdery_mildew",
    # 13. Strawberry (2)
    "Strawberry___Leaf_scorch",
    "Strawberry___healthy",
    # 14. Tomato (10)
    "Tomato___Bacterial_spot",
    "Tomato___Early_blight",
    "Tomato___Late_blight",
    "Tomato___Leaf_Mold",
    "Tomato___Septoria_leaf_spot",
    "Tomato___Spider_mites Two-spotted_spider_mite",
    "Tomato___Target_Spot",
    "Tomato___Tomato_Yellow_Leaf_Curl_Virus",
    "Tomato___Tomato_mosaic_virus",
    "Tomato___healthy",
]

# Mapping local raw directory names to canonical PlantVillage 38 names
LOCAL_TO_CANONICAL_MAP = {
    "Pepper__bell___Bacterial_spot": "Pepper,_bell___Bacterial_spot",
    "Pepper__bell___healthy": "Pepper,_bell___healthy",
    "Potato___Early_blight": "Potato___Early_blight",
    "Potato___Late_blight": "Potato___Late_blight",
    "Potato___healthy": "Potato___healthy",
    "Tomato_Bacterial_spot": "Tomato___Bacterial_spot",
    "Tomato_Early_blight": "Tomato___Early_blight",
    "Tomato_Late_blight": "Tomato___Late_blight",
    "Tomato_Leaf_Mold": "Tomato___Leaf_Mold",
    "Tomato_Septoria_leaf_spot": "Tomato___Septoria_leaf_spot",
    "Tomato_Spider_mites_Two_spotted_spider_mite": "Tomato___Spider_mites Two-spotted_spider_mite",
    "Tomato__Target_Spot": "Tomato___Target_Spot",
    "Tomato__Tomato_YellowLeaf__Curl_Virus": "Tomato___Tomato_Yellow_Leaf_Curl_Virus",
    "Tomato__Tomato_mosaic_virus": "Tomato___Tomato_mosaic_virus",
    "Tomato_healthy": "Tomato___healthy",
}


def compute_sha256(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest()


def is_valid_image(path: Path) -> bool:
    try:
        with Image.open(path) as img:
            img.verify()
        with Image.open(path) as img:
            img.convert("RGB")
            return img.size[0] >= 32 and img.size[1] >= 32
    except Exception:
        return False


def fetch_remote_samples(
    class_name: str,
    target_dir: Path,
    max_samples: int = 50,
) -> int:
    """
    Downloads legitimate benchmark samples from the official PlantVillage repository
    (https://github.com/spMohanty/PlantVillage-Dataset).
    """
    target_dir.mkdir(parents=True, exist_ok=True)
    api_url = f"https://api.github.com/repos/spMohanty/PlantVillage-Dataset/contents/raw/color/{urllib.request.quote(class_name)}"
    req = urllib.request.Request(
        api_url,
        headers={"User-Agent": "PlantScanAI-Benchmark/1.0 (research@plantscan.org)"},
    )

    try:
        with urllib.request.urlopen(req, timeout=12) as response:
            files_meta = json.loads(response.read().decode("utf-8"))
    except Exception as e:
        print(f"  Notice: Remote directory listing failed for {class_name}: {e}")
        return 0

    downloaded = 0
    valid_files = [f for f in files_meta if f.get("name", "").lower().endswith((".jpg", ".jpeg", ".png"))]
    random.seed(42)
    selected_files = random.sample(valid_files, min(len(valid_files), max_samples))

    for item in selected_files:
        dl_url = item.get("download_url")
        fname = item.get("name")
        if not dl_url or not fname:
            continue
        dest_path = target_dir / fname
        if dest_path.exists() and dest_path.stat().st_size > 0:
            downloaded += 1
            continue

        try:
            req_dl = urllib.request.Request(
                dl_url,
                headers={"User-Agent": "PlantScanAI-Benchmark/1.0 (research@plantscan.org)"},
            )
            with urllib.request.urlopen(req_dl, timeout=15) as dl_resp:
                content = dl_resp.read()
                with open(dest_path, "wb") as out_f:
                    out_f.write(content)
            if is_valid_image(dest_path):
                downloaded += 1
            else:
                dest_path.unlink(missing_ok=True)
            time.sleep(0.1)
        except Exception as e:
            print(f"  Download error for {fname}: {e}")
            dest_path.unlink(missing_ok=True)

    return downloaded


def prepare_benchmark(
    max_samples_per_class: int = 80,
    download_missing: bool = True,
) -> Dict:
    print("=" * 70)
    print("PlantScanAI - PlantVillage 38-Class Benchmark Preparation Pipeline")
    print(f"Target: 38 Classes, 14 Crop Species | Seed: 42")
    print("=" * 70)

    BENCHMARK_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    for split in ["train", "validation", "test"]:
        (BENCHMARK_OUTPUT_DIR / split).mkdir(parents=True, exist_ok=True)

    seen_hashes: Set[str] = set()
    duplicate_count = 0
    corrupt_count = 0

    class_stats = {}
    missing_classes = []
    locally_sourced = []
    remotely_sourced = []

    # Map existing local raw PlantVillage directories
    local_raw_dirs = {}
    if RAW_PLANTVILLAGE_DIR.exists():
        for d in RAW_PLANTVILLAGE_DIR.iterdir():
            if d.is_dir():
                canonical = LOCAL_TO_CANONICAL_MAP.get(d.name, d.name)
                local_raw_dirs[canonical] = d

    for cls_idx, cls_name in enumerate(PLANTVILLAGE_38_CLASSES, 1):
        print(f"[{cls_idx:02d}/38] Processing class: {cls_name}...")
        valid_class_images: List[Path] = []

        # 1. Check local repository
        if cls_name in local_raw_dirs:
            local_dir = local_raw_dirs[cls_name]
            candidates = sorted(list(local_dir.glob("*.jpg")) + list(local_dir.glob("*.png")) + list(local_dir.glob("*.JPG")))
            random.seed(42)
            random.shuffle(candidates)

            for cand in candidates:
                if len(valid_class_images) >= max_samples_per_class:
                    break
                if not is_valid_image(cand):
                    corrupt_count += 1
                    continue
                h = compute_sha256(cand)
                if h in seen_hashes:
                    duplicate_count += 1
                    continue
                seen_hashes.add(h)
                valid_class_images.append(cand)

            if valid_class_images:
                locally_sourced.append(cls_name)

        # 2. If missing or insufficient, fetch benchmark samples if enabled
        if len(valid_class_images) < 20 and download_missing:
            temp_cls_dir = PROJECT_ROOT / "datasets" / "raw" / "PlantVillage_Benchmark_Downloaded" / cls_name
            fetched = fetch_remote_samples(cls_name, temp_cls_dir, max_samples=max_samples_per_class)
            if fetched > 0:
                remotely_sourced.append(cls_name)
                for cand in temp_cls_dir.glob("*.*"):
                    if len(valid_class_images) >= max_samples_per_class:
                        break
                    if not is_valid_image(cand):
                        continue
                    h = compute_sha256(cand)
                    if h in seen_hashes:
                        duplicate_count += 1
                        continue
                    seen_hashes.add(h)
                    valid_class_images.append(cand)

        total_collected = len(valid_class_images)
        if total_collected == 0:
            missing_classes.append(cls_name)
            class_stats[cls_name] = {"train": 0, "validation": 0, "test": 0, "total": 0, "status": "MISSING_DATA"}
            print(f"  --> Status: MISSING (0 images)")
            continue

        # Stratified Split 70% Train, 15% Val, 15% Test
        random.seed(42 + cls_idx)
        random.shuffle(valid_class_images)

        n_test = max(1, int(round(total_collected * 0.15)))
        n_val = max(1, int(round(total_collected * 0.15)))
        n_train = total_collected - (n_test + n_val)
        if n_train <= 0:
            n_train = 1
            if n_test > 1:
                n_test -= 1

        train_imgs = valid_class_images[:n_train]
        val_imgs = valid_class_images[n_train:n_train + n_val]
        test_imgs = valid_class_images[n_train + n_val:]

        splits_map = {"train": train_imgs, "validation": val_imgs, "test": test_imgs}
        for split_name, imgs in splits_map.items():
            dest_dir = BENCHMARK_OUTPUT_DIR / split_name / cls_name
            dest_dir.mkdir(parents=True, exist_ok=True)
            for img_p in imgs:
                shutil.copy2(img_p, dest_dir / img_p.name)

        class_stats[cls_name] = {
            "train": len(train_imgs),
            "validation": len(val_imgs),
            "test": len(test_imgs),
            "total": total_collected,
            "status": "PREPARED",
        }
        print(f"  --> Prepared: {total_collected} images (Train: {len(train_imgs)}, Val: {len(val_imgs)}, Test: {len(test_imgs)})")

    # Compile comprehensive report
    total_train = sum(s["train"] for s in class_stats.values())
    total_val = sum(s["validation"] for s in class_stats.values())
    total_test = sum(s["test"] for s in class_stats.values())
    total_all = total_train + total_val + total_test

    manifest = {
        "benchmark_name": "PlantVillage 38-Class Authoritative Benchmark",
        "reference_standard": "Phase 1 Project Report (Mohanty et al., 2016)",
        "total_required_classes": 38,
        "total_crops": 14,
        "classes_prepared": len(PLANTVILLAGE_38_CLASSES) - len(missing_classes),
        "missing_classes_count": len(missing_classes),
        "missing_classes": missing_classes,
        "locally_sourced_classes": locally_sourced,
        "remotely_sourced_classes": remotely_sourced,
        "summary": {
            "train_images": total_train,
            "validation_images": total_val,
            "test_images": total_test,
            "total_images": total_all,
            "duplicate_images_filtered": duplicate_count,
            "corrupt_images_rejected": corrupt_count,
        },
        "crops_breakdown": {
            "Apple": 4,
            "Blueberry": 1,
            "Cherry": 2,
            "Corn_(maize)": 4,
            "Grape": 4,
            "Orange": 1,
            "Peach": 2,
            "Pepper,_bell": 2,
            "Potato": 3,
            "Raspberry": 1,
            "Soybean": 1,
            "Squash": 1,
            "Strawberry": 2,
            "Tomato": 10,
        },
        "class_details": class_stats,
        "provenance": {
            "primary_source": "PlantVillage Open Access Repository (Sharada Mohanty, Marcel Salathé, 2016)",
            "license": "Creative Commons Attribution-ShareAlike 4.0 International (CC BY-SA 4.0) / Public Domain",
            "repository_url": "https://github.com/spMohanty/PlantVillage-Dataset",
        },
    }

    REPORT_OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(REPORT_OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)

    print("\n" + "=" * 70)
    print(f"Benchmark Dataset Preparation Summary:")
    print(f"Total Prepared Classes: {manifest['classes_prepared']}/38 across 14 crops")
    print(f"Total Images: {total_all} (Train: {total_train}, Val: {total_val}, Test: {total_test})")
    print(f"Duplicates Blocked: {duplicate_count} | Corrupt Blocked: {corrupt_count}")
    print(f"Report written to: {REPORT_OUTPUT_PATH}")
    print("=" * 70)

    return manifest


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Prepare PlantVillage 38-Class Benchmark Dataset")
    parser.add_argument("--max_samples", type=int, default=50, help="Max images per class to prepare")
    parser.add_argument("--no_download", action="store_true", help="Disable remote fetching for missing classes")
    args = parser.parse_args()

    prepare_benchmark(
        max_samples_per_class=args.max_samples,
        download_missing=not args.no_download,
    )
