"""
PlantScanAI: Reproducible External Plant-Part Acquisition & Staging Workflow

Acquires authentic plant-part photographs from verified open-access repositories
(iNaturalist Open Data on AWS, strictly CC0 / CC-BY / CC-BY-SA licenses).
Applies automated integrity verification, perceptual duplicate screening against the
existing cleaned dataset, produces contact sheets, and stages approved images
with specimen-level grouping to prevent cross-split leakage.

Usage:
    python datasets/scripts/acquire_plant_parts.py --query      # Fetch candidates from API
    python datasets/scripts/acquire_plant_parts.py --review     # Generate contact sheets
    python datasets/scripts/acquire_plant_parts.py --stage      # Allocate approved candidates to staging splits
"""

import argparse
import csv
import io
import json
import math
import os
import shutil
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

import cv2
import numpy as np
import requests
from PIL import Image, ImageDraw, ImageFont

# Root Paths
BASE_DIR = Path(__file__).resolve().parent.parent.parent
DATASETS_DIR = BASE_DIR / "datasets"
ORIGINAL_DIR = DATASETS_DIR / "plant_parts"
CLEANED_DIR = DATASETS_DIR / "plant_parts_cleaned"
STAGING_DIR = DATASETS_DIR / "plant_parts_staging"
REPORTS_DIR = DATASETS_DIR / "reports"

CANDIDATES_DIR = STAGING_DIR / "candidates"
MANIFESTS_DIR = STAGING_DIR / "manifests"
CONTACT_SHEETS_DIR = STAGING_DIR / "contact_sheets"
APPROVED_DIR = STAGING_DIR / "approved"
REJECTED_DIR = STAGING_DIR / "rejected"
STAGING_REVIEW_FILE = REPORTS_DIR / "plant_parts_staging_review.json"

CLASSES = ["bark", "fruit", "leaf", "stem"]
TARGET_DISTRIBUTION = {
    "train": 70,
    "val": 15,
    "test": 15,
    "total": 100,
}

USER_AGENT = "PlantScanAI-Research/1.0 (academic open dataset remediation; contact: sagarnag774)"

# Target queries for each plant-part class
# Incorporates iNaturalist Controlled Terms:
# term_id=12, term_value_id=14 -> Confirmed "Fruits or Seeds"
# term_id=36, term_value_id=38 -> Confirmed "Green Leaves"
CROP_TAXA_QUERIES = {
    "fruit": [
        {"taxon_name": "Solanum lycopersicum", "common": "Tomato fruit on vine", "term_id": 12, "term_value_id": 14},
        {"taxon_name": "Malus domestica", "common": "Apple on tree branch", "term_id": 12, "term_value_id": 14},
        {"taxon_name": "Vitis vinifera", "common": "Grape cluster on vine", "term_id": 12, "term_value_id": 14},
        {"taxon_name": "Capsicum annuum", "common": "Sweet pepper on plant", "term_id": 12, "term_value_id": 14},
        {"taxon_name": "Citrus", "common": "Citrus on tree branch", "term_id": 12, "term_value_id": 14},
        {"taxon_name": "Fragaria", "common": "Strawberry fruit on plant", "term_id": 12, "term_value_id": 14},
        {"taxon_name": "Cucurbita", "common": "Squash / Pumpkin fruit", "term_id": 12, "term_value_id": 14},
    ],
    "stem": [
        {"taxon_name": "Phyllostachys", "common": "Bamboo culm internodes and rings"},
        {"taxon_name": "Equisetum hyemale", "common": "Rough horsetail jointed ribbed stem"},
        {"taxon_name": "Asparagus officinalis", "common": "Asparagus herbaceous main stem"},
        {"taxon_name": "Rheum", "common": "Rhubarb thick herbaceous stalk"},
        {"taxon_name": "Opuntia", "common": "Prickly pear succulent stem cladode", "q": "stem"},
    ],
    "bark": [
        {"taxon_name": "Betula pendula", "common": "Silver birch peeling bark", "q": "bark"},
        {"taxon_name": "Quercus robur", "common": "Oak furrowed trunk bark", "q": "bark"},
        {"taxon_name": "Pinus sylvestris", "common": "Scots pine trunk bark plates", "q": "bark"},
        {"taxon_name": "Eucalyptus", "common": "Eucalyptus peeling fibrous bark", "q": "bark"},
    ],
    "leaf": [
        {"taxon_name": "Acer", "common": "Maple foliar leaf", "term_id": 36, "term_value_id": 38},
        {"taxon_name": "Quercus", "common": "Oak foliar leaf", "term_id": 36, "term_value_id": 38},
        {"taxon_name": "Mangifera indica", "common": "Mango foliar leaf", "term_id": 36, "term_value_id": 38},
        {"taxon_name": "Gossypium", "common": "Cotton foliar leaf", "q": "leaf"},
    ],
}


def compute_sha256(data: bytes) -> str:
    import hashlib
    return hashlib.sha256(data).hexdigest()


def compute_dhash(gray_arr: np.ndarray, hash_size: int = 8) -> Tuple[int, str]:
    resized = cv2.resize(gray_arr, (hash_size + 1, hash_size), interpolation=cv2.INTER_AREA)
    diff = resized[:, 1:] > resized[:, :-1]
    binary_str = "".join(["1" if b else "0" for b in diff.flatten()])
    int_val = int(binary_str, 2)
    hex_val = f"{int_val:016x}"
    return int_val, hex_val


def hamming_distance(h1: int, h2: int) -> int:
    return bin(h1 ^ h2).count("1")


def load_cleaned_hashes() -> Tuple[Set[str], List[Dict[str, Any]]]:
    """Loads all SHA-256 and dHash values from the existing cleaned dataset."""
    sha_set = set()
    dhash_list = []

    if not CLEANED_DIR.exists():
        return sha_set, dhash_list

    for img_path in CLEANED_DIR.rglob("*.*"):
        if not img_path.suffix.lower() in [".jpg", ".jpeg", ".png"]:
            continue
        try:
            with open(img_path, "rb") as f:
                b = f.read()
            sha = compute_sha256(b)
            sha_set.add(sha)

            im = Image.open(io.BytesIO(b)).convert("RGB")
            arr = np.array(im)
            gray = cv2.cvtColor(arr, cv2.COLOR_RGB2GRAY)
            dh_int, _ = compute_dhash(gray)
            dhash_list.append({
                "path": str(img_path.relative_to(DATASETS_DIR)).replace("\\", "/"),
                "dhash_int": dh_int,
            })
        except Exception:
            continue

    return sha_set, dhash_list


def analyze_image_quality(img_bytes: bytes) -> Dict[str, Any]:
    """Evaluates image characteristics for quality, sharpness, and drawing detection."""
    try:
        im = Image.open(io.BytesIO(img_bytes))
        im.verify()
    except Exception as e:
        return {"corrupt": True, "error": str(e)}

    im = Image.open(io.BytesIO(img_bytes)).convert("RGB")
    w, h = im.size
    arr = np.array(im)
    gray = cv2.cvtColor(arr, cv2.COLOR_RGB2GRAY)
    hsv = cv2.cvtColor(arr, cv2.COLOR_RGB2HSV)

    lap_var = float(cv2.Laplacian(gray, cv2.CV_64F).var())
    dh_int, dh_hex = compute_dhash(gray)

    sat = hsv[:, :, 1]
    val = hsv[:, :, 2]
    paper_mask = (val > 210) & (sat < 45)
    paper_ratio = float(np.mean(paper_mask))

    edges = cv2.Canny(gray, 50, 150)
    edge_ratio = float(np.mean(edges > 0))

    sat_mean = float(np.mean(sat))
    val_mean = float(np.mean(val))

    reasons = []
    if lap_var < 35.0:
        reasons.append(f"Blur / low Laplacian variance ({lap_var:.1f} < 35)")
    if paper_ratio > 0.40 and sat_mean < 35.0:
        reasons.append(f"Potential drawing/page scan (paper={paper_ratio:.2f}, sat={sat_mean:.1f})")
    if edge_ratio > 0.20 and sat_mean < 30.0:
        reasons.append(f"High-contrast engraving edge density ({edge_ratio:.2f})")
    if min(w, h) < 300:
        reasons.append(f"Resolution too low ({w}x{h} < 300x300)")

    return {
        "corrupt": False,
        "width": w,
        "height": h,
        "lap_var": round(lap_var, 2),
        "paper_ratio": round(paper_ratio, 4),
        "edge_ratio": round(edge_ratio, 4),
        "sat_mean": round(sat_mean, 2),
        "val_mean": round(val_mean, 2),
        "dhash_int": dh_int,
        "dhash_hex": dh_hex,
        "passed_heuristics": len(reasons) == 0,
        "defect_reasons": reasons,
    }


def query_inaturalist_candidates(
    target_class: str,
    query_cfg: Dict[str, Any],
    count_needed: int,
    cleaned_shas: Set[str],
    cleaned_dhashes: List[Dict[str, Any]],
    staged_shas: Set[str],
    staged_obs_ids: Set[int],
) -> List[Dict[str, Any]]:
    """Fetches candidate research-grade photographs from iNaturalist Open Data."""
    candidates = []
    url = "https://api.inaturalist.org/v1/observations"

    params: Dict[str, Any] = {
        "taxon_name": query_cfg["taxon_name"],
        "quality_grade": "research",
        "photo_license": "cc-by,cc-by-sa,cc0",
        "per_page": 30,
        "order": "desc",
    }
    if "term_id" in query_cfg:
        params["term_id"] = query_cfg["term_id"]
        params["term_value_id"] = query_cfg["term_value_id"]
    elif "q" in query_cfg:
        params["q"] = query_cfg["q"]

    headers = {"User-Agent": USER_AGENT, "Connection": "close"}

    data = None
    for attempt in range(3):
        try:
            resp = requests.get(url, params=params, headers=headers, timeout=12)
            if resp.status_code == 200:
                data = resp.json()
                break
            else:
                time.sleep(1.0)
        except Exception:
            time.sleep(1.5)

    if not data:
        return candidates

    results = data.get("results", [])
    for obs in results:
        obs_id = obs["id"]
        if obs_id in staged_obs_ids:
            continue

        photos = obs.get("photos", [])
        if not photos:
            continue

        p = photos[0]
        raw_url = p.get("url")
        if not raw_url:
            continue

        medium_url = raw_url.replace("/square.", "/medium.").replace("/small.", "/medium.")
        license_code = p.get("license_code", "").lower()
        if license_code not in ["cc0", "cc-by", "cc-by-sa"]:
            continue

        attribution = p.get("attribution") or f"(c) iNaturalist user #{obs.get('user', {}).get('login', 'unknown')}"

        img_bytes = None
        for img_attempt in range(2):
            try:
                time.sleep(0.3)
                img_resp = requests.get(medium_url, headers=headers, timeout=10)
                if img_resp.status_code == 200:
                    img_bytes = img_resp.content
                    break
            except Exception:
                time.sleep(1.0)

        if not img_bytes:
            continue

        sha256 = compute_sha256(img_bytes)
        if sha256 in cleaned_shas or sha256 in staged_shas:
            continue

        qual = analyze_image_quality(img_bytes)
        if qual.get("corrupt") or not qual.get("passed_heuristics"):
            continue

        dh = qual["dhash_int"]
        is_near_dup = False
        for c_dh in cleaned_dhashes:
            if hamming_distance(dh, c_dh["dhash_int"]) <= 2:
                is_near_dup = True
                break
        if is_near_dup:
            continue

        candidate_info = {
            "observation_id": obs_id,
            "target_class": target_class,
            "taxon_name": query_cfg["taxon_name"],
            "common_name": query_cfg["common"],
            "photo_id": p.get("id"),
            "photo_url": medium_url,
            "observation_url": f"https://www.inaturalist.org/observations/{obs_id}",
            "license": license_code,
            "attribution": attribution,
            "sha256": sha256,
            "dhash_hex": qual["dhash_hex"],
            "dhash_int": qual["dhash_int"],
            "width": qual["width"],
            "height": qual["height"],
            "lap_var": qual["lap_var"],
            "paper_ratio": qual["paper_ratio"],
            "edge_ratio": qual["edge_ratio"],
            "sat_mean": qual["sat_mean"],
            "img_bytes": img_bytes,
        }
        candidates.append(candidate_info)
        staged_shas.add(sha256)
        staged_obs_ids.add(obs_id)

        if len(candidates) >= count_needed:
            break

    return candidates


def run_acquisition_workflow(target_total_per_class: int = 100):
    """Executes candidate acquisition, screening, and staging."""
    print("=" * 80)
    print("PLANTSCAN AI: REPRODUCIBLE PLANT-PART DATASET ACQUISITION WORKFLOW")
    print("=" * 80)

    CANDIDATES_DIR.mkdir(parents=True, exist_ok=True)
    MANIFESTS_DIR.mkdir(parents=True, exist_ok=True)
    CONTACT_SHEETS_DIR.mkdir(parents=True, exist_ok=True)
    APPROVED_DIR.mkdir(parents=True, exist_ok=True)
    REJECTED_DIR.mkdir(parents=True, exist_ok=True)

    cleaned_shas, cleaned_dhashes = load_cleaned_hashes()
    print(f"Loaded existing cleaned dataset index: {len(cleaned_shas)} unique SHA-256 hashes.")

    cleaned_counts = {
        "bark": {"train": 63, "val": 14, "test": 15, "total": 92},
        "leaf": {"train": 65, "val": 11, "test": 15, "total": 91},
        "fruit": {"train": 19, "val": 2, "test": 3, "total": 24},
        "stem": {"train": 24, "val": 7, "test": 3, "total": 34},
    }

    manifest_file = MANIFESTS_DIR / "staging_manifest.json"
    existing_manifest = []
    if manifest_file.exists():
        with open(manifest_file, "r", encoding="utf-8") as f:
            existing_manifest = json.load(f)

    staged_shas = {item["sha256"] for item in existing_manifest}
    staged_obs_ids = {item["observation_id"] for item in existing_manifest}

    staged_counts_by_class = {c: 0 for c in CLASSES}
    for item in existing_manifest:
        if item.get("target_class") in staged_counts_by_class:
            staged_counts_by_class[item["target_class"]] += 1

    all_candidates = list(existing_manifest)

    for cls in CLASSES:
        current_total = cleaned_counts[cls]["total"] + staged_counts_by_class[cls]
        deficit = max(0, target_total_per_class - current_total)
        # Query 2x deficit to allow strict visual curation
        fetch_target = math.ceil(deficit * 1.5) if deficit > 0 else 0

        print(f"\n[{cls.upper()}] Cleaned: {cleaned_counts[cls]['total']}, Staged: {staged_counts_by_class[cls]}, Target: {target_total_per_class} -> Needed: {deficit} (Querying for {fetch_target})")

        if fetch_target <= 0:
            print(f"  Target already reached for class '{cls}'.")
            continue

        cls_dir = CANDIDATES_DIR / cls
        cls_dir.mkdir(parents=True, exist_ok=True)

        queries = CROP_TAXA_QUERIES.get(cls, [])
        per_query_target = math.ceil(fetch_target / len(queries)) if queries else 0

        acquired_for_class = 0
        for q_cfg in queries:
            needed = min(per_query_target, fetch_target - acquired_for_class)
            if needed <= 0:
                break
            print(f"  Querying: {q_cfg['taxon_name']} ({q_cfg['common']}) for ~{needed} items...")
            found = query_inaturalist_candidates(
                target_class=cls,
                query_cfg=q_cfg,
                count_needed=needed,
                cleaned_shas=cleaned_shas,
                cleaned_dhashes=cleaned_dhashes,
                staged_shas=staged_shas,
                staged_obs_ids=staged_obs_ids,
            )
            print(f"    -> Acquired {len(found)} candidate photos.")

            for item in found:
                cand_id = f"staged_{cls}_{item['observation_id']}_{item['photo_id']}"
                file_name = f"{cand_id}.jpg"
                save_path = cls_dir / file_name

                with open(save_path, "wb") as f:
                    f.write(item.pop("img_bytes"))

                item["candidate_id"] = cand_id
                item["relative_path"] = f"candidates/{cls}/{file_name}"
                item["status"] = "staged_candidate"
                all_candidates.append(item)
                acquired_for_class += 1

            time.sleep(1.0)

    with open(manifest_file, "w", encoding="utf-8") as f:
        json.dump(all_candidates, f, indent=2)

    manifest_csv = MANIFESTS_DIR / "staging_manifest.csv"
    if all_candidates:
        keys = [k for k in all_candidates[0].keys() if k != "dhash_int"]
        with open(manifest_csv, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=keys)
            writer.writeheader()
            for row in all_candidates:
                writer.writerow({k: row.get(k, "") for k in keys})

    print(f"\n[OK] Staging manifest written: {len(all_candidates)} total candidates recorded.")
    generate_staging_contact_sheets()
    summarize_staging_progress(cleaned_counts, all_candidates)


def generate_staging_contact_sheets():
    """Generates visual contact sheets for all staged candidates."""
    print("\nGenerating visual contact sheets for staged candidates...")
    thumb_size = (160, 160)
    label_h = 32
    cell_w = thumb_size[0] + 12
    cell_h = thumb_size[1] + label_h + 12

    for cls in CLASSES:
        cls_dir = CANDIDATES_DIR / cls
        if not cls_dir.exists():
            continue
        files = sorted(list(cls_dir.glob("*.jpg")) + list(cls_dir.glob("*.png")))
        if not files:
            continue

        n = len(files)
        cols = 8 if n >= 24 else 4
        rows = math.ceil(n / cols)

        sheet_w = 20 + cols * cell_w
        sheet_h = 45 + rows * cell_h
        sheet = Image.new("RGB", (sheet_w, sheet_h), color=(30, 30, 30))
        draw = ImageDraw.Draw(sheet)

        draw.text(
            (15, 12),
            f"PlantScanAI Staged Candidates: Class '{cls.upper()}' ({n} images)",
            fill=(240, 240, 240),
        )

        for idx, f in enumerate(files):
            r = idx // cols
            c = idx % cols
            x = 10 + c * cell_w + 6
            y = 40 + r * cell_h + 6

            try:
                with Image.open(f) as im:
                    thumb = im.convert("RGB").resize(thumb_size, Image.Resampling.BILINEAR)
                sheet.paste(thumb, (x, y))
                lbl = f.stem.replace(f"staged_{cls}_", "")[:18]
                draw.text((x + 2, y + thumb_size[1] + 4), lbl, fill=(180, 220, 180))
            except Exception:
                draw.rectangle([x, y, x + thumb_size[0], y + thumb_size[1]], fill=(120, 20, 20))
                draw.text((x + 5, y + 20), "CORRUPT", fill=(255, 255, 255))

        out_file = CONTACT_SHEETS_DIR / f"contact_sheet_staged_{cls}.jpg"
        sheet.save(out_file, format="JPEG", quality=85)
        print(f"  Saved contact sheet: {out_file.name} ({n} candidates)")


def summarize_staging_progress(cleaned_counts: Dict[str, Any], candidates: List[Dict[str, Any]]):
    """Outputs summary report of current inventory + staged candidates against target."""
    staged_by_class = {c: 0 for c in CLASSES}
    for cand in candidates:
        staged_by_class[cand["target_class"]] += 1

    print("\n" + "=" * 80)
    print("PLANTSCAN AI: DATASET ACQUISITION & STAGING PROGRESS SUMMARY")
    print("=" * 80)
    print(f"{'Class':8s} | {'Cleaned':7s} | {'Staged':7s} | {'Combined':8s} | {'Target':6s} | {'Deficit/Surplus':15s}")
    print("-" * 80)

    for cls in CLASSES:
        cl_tot = cleaned_counts[cls]["total"]
        st_tot = staged_by_class[cls]
        comb = cl_tot + st_tot
        target = TARGET_DISTRIBUTION["total"]
        diff = comb - target
        status_str = f"+{diff} surplus" if diff >= 0 else f"{diff} needed"
        print(f"{cls:8s} | {cl_tot:7d} | {st_tot:7d} | {comb:8d} | {target:6d} | {status_str:15s}")

    total_cleaned = sum(cleaned_counts[c]["total"] for c in CLASSES)
    total_staged = sum(staged_by_class[c] for c in CLASSES)
    total_combined = total_cleaned + total_staged
    print("-" * 80)
    print(f"{'TOTAL':8s} | {total_cleaned:7d} | {total_staged:7d} | {total_combined:8d} | {400:6d} | {total_combined - 400:+d}")
    print("=" * 80)


def allocate_staging_to_splits():
    """
    Allocates approved staged candidates into train, val, and test splits
    to fulfill the target distribution (70 Train, 15 Val, 15 Test per class).
    Enforces atomic observation_id grouping: all photos from the same observation
    are placed into the same split to prevent data leakage.
    """
    manifest_file = MANIFESTS_DIR / "staging_manifest.json"
    if not manifest_file.exists():
        print("[ERROR] Staging manifest not found. Run --query first.")
        return

    with open(manifest_file, "r", encoding="utf-8") as f:
        candidates = json.load(f)

    # Load review overrides if present
    reviews = {}
    if STAGING_REVIEW_FILE.exists():
        with open(STAGING_REVIEW_FILE, "r", encoding="utf-8") as f:
            reviews = json.load(f)

    cleaned_counts = {
        "bark": {"train": 63, "val": 14, "test": 15},
        "leaf": {"train": 65, "val": 11, "test": 15},
        "fruit": {"train": 19, "val": 2, "test": 3},
        "stem": {"train": 24, "val": 7, "test": 3},
    }

    obs_groups: Dict[str, Dict[int, List[Dict[str, Any]]]] = {c: {} for c in CLASSES}
    for cand in candidates:
        cand_id = cand["candidate_id"]
        # Check review verdict
        rev = reviews.get(cand_id, {})
        verdict = rev.get("status", "approve")
        if verdict == "reject":
            continue

        cls = cand["target_class"]
        obs_id = cand["observation_id"]
        obs_groups[cls].setdefault(obs_id, []).append(cand)

    if APPROVED_DIR.exists():
        shutil.rmtree(APPROVED_DIR)
    APPROVED_DIR.mkdir(parents=True, exist_ok=True)

    approved_manifest = []

    print("\nAllocating approved candidates to staging splits (enforcing observation_id isolation)...")
    for cls in CLASSES:
        train_needed = max(0, TARGET_DISTRIBUTION["train"] - cleaned_counts[cls]["train"])
        val_needed = max(0, TARGET_DISTRIBUTION["val"] - cleaned_counts[cls]["val"])
        test_needed = max(0, TARGET_DISTRIBUTION["test"] - cleaned_counts[cls]["test"])

        print(f"\n[{cls.upper()}] Deficits: Train=+{train_needed}, Val=+{val_needed}, Test=+{test_needed}")

        allocated_counts = {"train": 0, "val": 0, "test": 0}

        for obs_id, cand_list in obs_groups[cls].items():
            if allocated_counts["test"] < test_needed:
                target_split = "test"
            elif allocated_counts["val"] < val_needed:
                target_split = "val"
            elif allocated_counts["train"] < train_needed:
                target_split = "train"
            else:
                # Target deficit fulfilled for this class
                break

            for cand in cand_list:
                src_path = STAGING_DIR / cand["relative_path"]
                if not src_path.exists():
                    continue

                dst_dir = APPROVED_DIR / target_split / cls
                dst_dir.mkdir(parents=True, exist_ok=True)
                dst_file = dst_dir / src_path.name
                shutil.copy2(src_path, dst_file)

                cand_record = dict(cand)
                cand_record["approved_split"] = target_split
                cand_record["approved_path"] = str(dst_file.relative_to(STAGING_DIR)).replace("\\", "/")
                approved_manifest.append(cand_record)
                allocated_counts[target_split] += 1

        print(f"  Allocated for {cls}: Train=+{allocated_counts['train']}, Val=+{allocated_counts['val']}, Test=+{allocated_counts['test']} (Total Staged: {sum(allocated_counts.values())})")

    # Stage rejected candidates to REJECTED_DIR
    if REJECTED_DIR.exists():
        shutil.rmtree(REJECTED_DIR)
    REJECTED_DIR.mkdir(parents=True, exist_ok=True)

    rejected_manifest = []
    for cand in candidates:
        cid = cand["candidate_id"]
        rev = reviews.get(cid, {})
        if rev.get("status") == "reject":
            src_path = STAGING_DIR / cand["relative_path"]
            if src_path.exists():
                dst_dir = REJECTED_DIR / cand["target_class"]
                dst_dir.mkdir(parents=True, exist_ok=True)
                dst_file = dst_dir / src_path.name
                shutil.copy2(src_path, dst_file)
                r_rec = dict(cand)
                r_rec["rejection_reason"] = rev.get("notes", "Rejected during visual curation")
                r_rec["rejected_path"] = str(dst_file.relative_to(STAGING_DIR)).replace("\\", "/")
                rejected_manifest.append(r_rec)

    approved_manifest_path = MANIFESTS_DIR / "approved_staging_manifest.json"
    with open(approved_manifest_path, "w", encoding="utf-8") as f:
        json.dump(approved_manifest, f, indent=2)

    approved_manifest_csv = MANIFESTS_DIR / "approved_staging_manifest.csv"
    if approved_manifest:
        keys = [k for k in approved_manifest[0].keys() if k != "dhash_int"]
        with open(approved_manifest_csv, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=keys)
            writer.writeheader()
            for row in approved_manifest:
                writer.writerow({k: row.get(k, "") for k in keys})

    rejected_manifest_path = MANIFESTS_DIR / "rejected_staging_manifest.json"
    with open(rejected_manifest_path, "w", encoding="utf-8") as f:
        json.dump(rejected_manifest, f, indent=2)

    print(f"\n[OK] Staging allocation complete.")
    print(f"     Approved & staged: {len(approved_manifest)} photos -> {APPROVED_DIR}")
    print(f"     Rejected & quarantined: {len(rejected_manifest)} candidates -> {REJECTED_DIR}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="PlantScanAI Dataset Acquisition Workflow")
    parser.add_argument("--query", action="store_true", help="Query iNaturalist API and download candidates")
    parser.add_argument("--review", action="store_true", help="Generate contact sheets and report")
    parser.add_argument("--stage", action="store_true", help="Allocate candidates into staging splits")
    parser.add_argument("--target", type=int, default=100, help="Target total photographs per class (default: 100)")

    args = parser.parse_args()

    if args.query:
        run_acquisition_workflow(target_total_per_class=args.target)
    elif args.review:
        generate_staging_contact_sheets()
    elif args.stage:
        allocate_staging_to_splits()
    else:
        parser.print_help()
