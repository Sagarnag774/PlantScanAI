"""
PlantScan AI - Stage 1 Plant-Part Dataset Preparation Pipeline
Builds a curated, verified 4-class anatomical dataset (bark, fruit, leaf, stem)
with clean 70/15/15 train/val/test stratified partitions and SHA-256 deduplication.
"""

import hashlib
import io
import json
import os
import random
import time
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Dict, List, Set
from PIL import Image

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATASET_DIR = PROJECT_ROOT / "datasets" / "plant_parts"
REPORTS_DIR = PROJECT_ROOT / "datasets" / "reports"
SEED = 42

random.seed(SEED)

CLASSES = ["bark", "fruit", "leaf", "stem"]
TARGET_PER_CLASS = 100

USER_AGENT = "PlantScanAI-Research/1.0 (https://github.com/Sagarnag774/PlantScanAI; research@plantscan.org)"


def compute_sha256(image: Image.Image) -> str:
    buf = io.BytesIO()
    image.save(buf, format="JPEG")
    return hashlib.sha256(buf.getvalue()).hexdigest()


def fetch_wikimedia_images(query: str, target_count: int, seen_hashes: Set[str]) -> List[Image.Image]:
    encoded_query = urllib.parse.quote(query)
    images = []
    offset = 0
    batch_size = 25

    while len(images) < target_count and offset < 150:
        url = (
            f"https://commons.wikimedia.org/w/api.php?action=query&format=json"
            f"&generator=search&gsrnamespace=6&gsrsearch={encoded_query}"
            f"&gsrlimit={batch_size}&gsroffset={offset}&prop=imageinfo&iiprop=url|mime"
        )
        try:
            req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
            with urllib.request.urlopen(req, timeout=15) as resp:
                data = json.loads(resp.read().decode("utf-8"))
        except Exception as e:
            print(f"  [API Warning] query '{query}' offset {offset}: {e}")
            time.sleep(2.0)
            break

        pages = data.get("query", {}).get("pages", {})
        if not pages:
            break

        for pid, pinfo in pages.items():
            if len(images) >= target_count:
                break
            infos = pinfo.get("imageinfo", [])
            if not infos:
                continue
            img_url = infos[0].get("url", "")
            mime = infos[0].get("mime", "").lower()
            if not any(ext in mime for ext in ["jpeg", "jpg", "png", "webp"]):
                continue

            try:
                img_req = urllib.request.Request(img_url, headers={"User-Agent": USER_AGENT})
                with urllib.request.urlopen(img_req, timeout=15) as img_resp:
                    raw_bytes = img_resp.read()
                im = Image.open(io.BytesIO(raw_bytes)).convert("RGB")
                if im.width < 120 or im.height < 120:
                    continue
                im_resized = im.resize((224, 224), Image.Resampling.LANCZOS)
                h = compute_sha256(im_resized)
                if h in seen_hashes:
                    continue
                seen_hashes.add(h)
                images.append(im_resized)
            except Exception:
                continue

        offset += batch_size
        time.sleep(1.0)  # Respect rate limit

    return images


def collect_local_leaf_images(target_count: int, seen_hashes: Set[str]) -> List[Image.Image]:
    images = []
    crops = ["apple", "banana", "bell_pepper", "cotton", "grape", "maize", "mango", "potato", "rice", "tomato"]
    per_crop = max(5, target_count // len(crops) + 2)

    for crop in crops:
        crop_dir = PROJECT_ROOT / "datasets" / "model" / crop / "train"
        if not crop_dir.exists():
            continue
        all_imgs = []
        for class_dir in crop_dir.iterdir():
            if class_dir.is_dir():
                all_imgs.extend(list(class_dir.glob("*.jpg")) + list(class_dir.glob("*.JPG")) + list(class_dir.glob("*.png")))
        random.shuffle(all_imgs)
        for p in all_imgs[:per_crop]:
            try:
                im = Image.open(p).convert("RGB").resize((224, 224), Image.Resampling.LANCZOS)
                h = compute_sha256(im)
                if h not in seen_hashes:
                    seen_hashes.add(h)
                    images.append(im)
                    if len(images) >= target_count:
                        return images
            except Exception:
                continue
    return images


def collect_local_stem_images(target_count: int, seen_hashes: Set[str]) -> List[Image.Image]:
    images = []
    # 1. Rice Sheath Blight (lesions on sheath / stem)
    sheath_dir = PROJECT_ROOT / "datasets" / "raw" / "Rice" / "Sheath Blight"
    if sheath_dir.exists():
        cand = list(sheath_dir.glob("*.jpg")) + list(sheath_dir.glob("*.JPG"))
        random.shuffle(cand)
        for p in cand[:35]:
            try:
                im = Image.open(p).convert("RGB").resize((224, 224), Image.Resampling.LANCZOS)
                h = compute_sha256(im)
                if h not in seen_hashes:
                    seen_hashes.add(h)
                    images.append(im)
            except Exception:
                continue

    # 2. Mango Die Back (mango tree branch/twig/stem necrosis)
    dieback_dir = PROJECT_ROOT / "datasets" / "raw" / "Mango" / "Die Back"
    if dieback_dir.exists():
        cand2 = list(dieback_dir.glob("*.jpg")) + list(dieback_dir.glob("*.JPG"))
        random.shuffle(cand2)
        for p in cand2[:35]:
            try:
                im = Image.open(p).convert("RGB").resize((224, 224), Image.Resampling.LANCZOS)
                h = compute_sha256(im)
                if h not in seen_hashes:
                    seen_hashes.add(h)
                    images.append(im)
            except Exception:
                continue

    return images


def build_plant_parts_dataset():
    print("=" * 65)
    print("PlantScan AI: Building Stage 1 Plant-Part Dataset (4 Classes)")
    print(f"Target: {TARGET_PER_CLASS} images per class (Bark, Fruit, Leaf, Stem)")
    print("=" * 65)

    seen_hashes: Set[str] = set()
    dataset_records: Dict[str, List[Image.Image]] = {}

    # 1. Collect LEAF images (from verified local multi-crop repository)
    print("\n[1/4] Collecting Leaf images from local multi-crop repository...")
    leaf_imgs = collect_local_leaf_images(TARGET_PER_CLASS, seen_hashes)
    print(f"  -> Collected {len(leaf_imgs)} leaf images.")
    dataset_records["leaf"] = leaf_imgs

    # 2. Collect BARK images (from open-access botanical tree bark repositories)
    print("\n[2/4] Collecting Bark images (Wikimedia Commons botanical archives)...")
    bark_queries = [
        "tree bark texture",
        "rough tree trunk bark",
        "pine tree bark trunk",
        "oak tree bark texture",
        "birch bark texture",
        "tree trunk wood bark",
    ]
    bark_imgs = []
    for q in bark_queries:
        needed = TARGET_PER_CLASS - len(bark_imgs)
        if needed <= 0:
            break
        print(f"  Searching: '{q}' (needed: {needed})...")
        bark_imgs.extend(fetch_wikimedia_images(q, needed, seen_hashes))
    print(f"  -> Collected {len(bark_imgs)} bark images.")
    dataset_records["bark"] = bark_imgs

    # 3. Collect FRUIT images (tomatoes, apples, grapes, bell peppers, citrus on plants)
    print("\n[3/4] Collecting Fruit images...")
    fruit_queries = [
        "apple fruit on branch tree",
        "ripe tomato on vine",
        "grape cluster on vine",
        "citrus fruit on tree",
        "mango fruit tree branch",
        "bell pepper fruit plant",
        "strawberry fruit on plant",
    ]
    fruit_imgs = []
    for q in fruit_queries:
        needed = TARGET_PER_CLASS - len(fruit_imgs)
        if needed <= 0:
            break
        print(f"  Searching: '{q}' (needed: {needed})...")
        fruit_imgs.extend(fetch_wikimedia_images(q, needed, seen_hashes))
    print(f"  -> Collected {len(fruit_imgs)} fruit images.")
    dataset_records["fruit"] = fruit_imgs

    # 4. Collect STEM images (plant stems, corn stalks, rice sheaths, bamboo culms, rose stems)
    print("\n[4/4] Collecting Stem images (local agronomic rice/mango + botanical stems)...")
    stem_imgs = collect_local_stem_images(50, seen_hashes)
    print(f"  -> Collected {len(stem_imgs)} local agricultural stem/stalk images.")
    stem_queries = [
        "plant stem stalk node",
        "corn stalk stem",
        "bamboo culm stem node",
        "green plant stem shoot",
        "sunflower stem stalk",
        "vine stem shoot tendril",
    ]
    for q in stem_queries:
        needed = TARGET_PER_CLASS - len(stem_imgs)
        if needed <= 0:
            break
        print(f"  Searching: '{q}' (needed: {needed})...")
        stem_imgs.extend(fetch_wikimedia_images(q, needed, seen_hashes))
    print(f"  -> Collected {len(stem_imgs)} stem images.")
    dataset_records["stem"] = stem_imgs

    # Partition into train/val/test
    print("\n" + "=" * 65)
    print("Partitioning into 70% Train, 15% Validation, 15% Test Splits...")
    print("=" * 65)

    summary = {}
    for c in CLASSES:
        imgs = dataset_records.get(c, [])
        random.shuffle(imgs)
        n = len(imgs)
        n_train = int(n * 0.70)
        n_val = int(n * 0.15)
        n_test = n - n_train - n_val

        splits = {
            "train": imgs[:n_train],
            "val": imgs[n_train : n_train + n_val],
            "test": imgs[n_train + n_val :],
        }

        summary[c] = {
            "total": n,
            "train": len(splits["train"]),
            "val": len(splits["val"]),
            "test": len(splits["test"]),
        }

        for split_name, split_imgs in splits.items():
            split_dir = DATASET_DIR / split_name / c
            split_dir.mkdir(parents=True, exist_ok=True)
            for idx, img in enumerate(split_imgs):
                out_path = split_dir / f"{c}_{idx:04d}.jpg"
                img.save(out_path, format="JPEG", quality=92)

        print(f"  [{c.upper():5s}] Total: {n:3d} -> Train: {summary[c]['train']:3d}, Val: {summary[c]['val']:2d}, Test: {summary[c]['test']:2d}")

    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    report_file = REPORTS_DIR / "plant_parts_dataset_report.json"
    with open(report_file, "w", encoding="utf-8") as f:
        json.dump(
            {
                "classes": CLASSES,
                "target_per_class": TARGET_PER_CLASS,
                "summary": summary,
                "split_ratio": {"train": 0.70, "val": 0.15, "test": 0.15},
                "image_resolution": "224x224",
                "format": "JPEG",
                "sources": [
                    "PlantScan AI Verified Multi-Crop Foliar Repository (Leaves, Rice Sheaths, Mango Twigs)",
                    "Wikimedia Commons CC-BY/CC-BY-SA/Public Domain Botanical Archives (Bark, Fruit, Stem)",
                ],
            },
            f,
            indent=2,
        )

    print(f"\n[OK] Dataset successfully built at: {DATASET_DIR}")
    print(f"[OK] Summary report saved at: {report_file}")


if __name__ == "__main__":
    build_plant_parts_dataset()
