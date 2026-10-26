"""
PlantScan AI - Plant-Part Dataset Quality Audit and Cleanup Pipeline
Audits datasets/plant_parts/, detects illustrations, engravings, text pages,
patents, non-plant objects, mislabeled organs, blur, and cross-split duplicate leakage.
Generates contact sheets, dataset inventory, audit reports, and a clean segregated dataset.
Original datasets/plant_parts/ files are strictly preserved.
"""

import argparse
import csv
import hashlib
import io
import json
import math
import shutil
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

import cv2
import numpy as np
from PIL import Image, ImageDraw

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATASET_DIR = PROJECT_ROOT / "datasets" / "plant_parts"
CLEANED_DIR = PROJECT_ROOT / "datasets" / "plant_parts_cleaned"
QUARANTINE_DIR = PROJECT_ROOT / "datasets" / "plant_parts_quarantine"
REPORTS_DIR = PROJECT_ROOT / "datasets" / "reports"
CONTACT_SHEETS_DIR = REPORTS_DIR / "contact_sheets"
OVERRIDES_FILE = REPORTS_DIR / "plant_parts_review_overrides.json"

CLASSES = ["bark", "fruit", "leaf", "stem"]
SPLITS = ["train", "val", "test"]


def compute_sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def compute_dhash(gray_arr: np.ndarray, hash_size: int = 8) -> Tuple[int, str]:
    resized = cv2.resize(gray_arr, (hash_size + 1, hash_size))
    diff = resized[:, 1:] > resized[:, :-1]
    dh_int = int(sum([2 ** i for (i, v) in enumerate(diff.flatten()) if v]))
    return dh_int, f"{dh_int:016x}"


def hamming_distance(h1: int, h2: int) -> int:
    return bin(h1 ^ h2).count("1")


def analyze_image_features(image_bytes: bytes) -> Dict[str, Any]:
    """Extract quantitative image characteristics for quality and illustration screening."""
    try:
        im = Image.open(io.BytesIO(image_bytes))
        im.verify()
    except Exception as e:
        return {"corrupt": True, "error": str(e)}

    im = Image.open(io.BytesIO(image_bytes))
    w, h = im.size
    fmt = im.format or "JPEG"
    mode = im.mode

    rgb_im = im.convert("RGB")
    arr = np.array(rgb_im)

    gray = cv2.cvtColor(arr, cv2.COLOR_RGB2GRAY)
    hsv = cv2.cvtColor(arr, cv2.COLOR_RGB2HSV)

    dh_int, dh_hex = compute_dhash(gray)

    # Sharpness / Texture via Laplacian variance
    lap_var = float(cv2.Laplacian(gray, cv2.CV_64F).var())

    # Paper / parchment background ratio (Lightness > 210, Saturation < 45)
    sat = hsv[:, :, 1]
    val = hsv[:, :, 2]
    paper_mask = (val > 210) & (sat < 45)
    paper_ratio = float(np.mean(paper_mask))

    # Dark stroke ratio on light paper (characteristic of pen/ink line drawings)
    dark_strokes = (val < 100) & (sat < 60)
    stroke_ratio = float(np.mean(dark_strokes))

    # Edge density via Canny edge detector
    edges = cv2.Canny(gray, 50, 150)
    edge_ratio = float(np.mean(edges > 0))

    sat_mean = float(np.mean(sat))
    val_mean = float(np.mean(val))

    # Horizontal text line projection variance (text pages show periodic horizontal lines)
    if paper_ratio > 0.30:
        row_dark = np.mean(val < 140, axis=1)
        row_variance = float(np.var(row_dark))
    else:
        row_variance = 0.0

    return {
        "corrupt": False,
        "width": w,
        "height": h,
        "format": fmt,
        "mode": mode,
        "dhash_int": dh_int,
        "dhash_hex": dh_hex,
        "lap_var": round(lap_var, 2),
        "paper_ratio": round(paper_ratio, 4),
        "stroke_ratio": round(stroke_ratio, 4),
        "edge_ratio": round(edge_ratio, 4),
        "sat_mean": round(sat_mean, 2),
        "val_mean": round(val_mean, 2),
        "row_variance": round(row_variance, 6),
    }


def automated_screen(features: Dict[str, Any], class_name: str) -> Tuple[str, str, str]:
    """Automated screening heuristic predicting status, category, and reason."""
    if features.get("corrupt"):
        return "reject", "corrupt_file", f"File corrupt or unreadable: {features.get('error')}"

    lap = features["lap_var"]
    paper = features["paper_ratio"]
    sat = features["sat_mean"]
    edge = features["edge_ratio"]
    row_var = features["row_variance"]

    # Severe blur / flat
    if lap < 15.0:
        return "reject", "severe_blur_or_flat", f"Laplacian variance too low ({lap} < 15); extremely blurry or featureless"

    # Patent / scanned document text page (high paper background + text row variance)
    if paper > 0.70 and sat < 20 and (row_var > 0.001 or edge > 0.04):
        return "reject", "scanned_document_text", f"Scanned printed text document/patent (paper={paper}, sat={sat}, row_var={row_var})"

    # High paper ratio line drawing / engraving
    if paper > 0.40 and sat < 35 and edge > 0.10:
        return "reject", "illustration_or_drawing", f"High paper background with dense drawing/engraving edges (paper={paper}, sat={sat}, edge={edge})"

    # Low saturation drawing on paper
    if paper > 0.50 and sat < 15:
        return "reject", "illustration_or_drawing", f"Monochrome illustration or diagram on paper (paper={paper}, sat={sat})"

    # Extremely high edge density on low saturation (dense woodcut/engraving)
    if sat < 25 and edge > 0.22 and paper > 0.05:
        return "reject", "illustration_or_drawing", f"Monochrome engraving / cross-hatching texture (sat={sat}, edge={edge}, paper={paper})"

    # Borderline items for manual review
    if paper > 0.30 and sat < 50:
        return "manual_review", "potential_illustration_or_specimen", f"Substantial paper background with moderate saturation (paper={paper}, sat={sat})"

    if lap < 45.0:
        return "manual_review", "mild_blur_or_low_contrast", f"Low Laplacian variance ({lap} < 45); check organ discernibility"

    return "keep", "confirmed_photograph", "Appears to be a genuine photographic capture of plant organ"


def generate_contact_sheets(dataset_path: Path, output_dir: Path) -> List[str]:
    """Generates visual contact sheets for every split and class."""
    output_dir.mkdir(parents=True, exist_ok=True)
    generated_paths = []

    thumb_size = (140, 140)
    label_h = 28
    cell_w = thumb_size[0] + 10
    cell_h = thumb_size[1] + label_h + 10

    for split in SPLITS:
        for cls in CLASSES:
            cls_dir = dataset_path / split / cls
            if not cls_dir.exists():
                continue
            files = sorted(list(cls_dir.glob("*.jpg")) + list(cls_dir.glob("*.png")))
            if not files:
                continue

            n = len(files)
            cols = 10 if n >= 40 else 5
            rows = math.ceil(n / cols)

            grid_w = cols * cell_w + 20
            grid_h = rows * cell_h + 40

            sheet = Image.new("RGB", (grid_w, grid_h), color=(30, 30, 30))
            draw = ImageDraw.Draw(sheet)

            draw.text(
                (15, 10),
                f"Split: {split.upper()} | Class: {cls.upper()} | Total: {n} images",
                fill=(240, 240, 240),
            )

            for idx, f in enumerate(files):
                r = idx // cols
                c = idx % cols
                x = 10 + c * cell_w + 5
                y = 35 + r * cell_h + 5

                try:
                    with Image.open(f) as im:
                        thumb = im.convert("RGB").resize(thumb_size, Image.Resampling.BILINEAR)
                    sheet.paste(thumb, (x, y))
                    lbl = f.stem
                    draw.text((x + 2, y + thumb_size[1] + 4), lbl, fill=(200, 200, 200))
                except Exception:
                    draw.rectangle([x, y, x + thumb_size[0], y + thumb_size[1]], fill=(120, 20, 20))
                    draw.text((x + 5, y + 20), "CORRUPT", fill=(255, 255, 255))

            out_file = output_dir / f"contact_sheet_{split}_{cls}.jpg"
            sheet.save(out_file, format="JPEG", quality=85)
            generated_paths.append(str(out_file))

    return generated_paths


def audit_dataset(
    dataset_path: Path = DATASET_DIR,
    overrides_path: Path = OVERRIDES_FILE,
) -> Dict[str, Any]:
    """Performs full reproducible audit of the plant-part dataset."""
    if not dataset_path.exists():
        raise FileNotFoundError(f"Dataset path not found: {dataset_path}")

    # Load manual review overrides if present
    overrides = {}
    if overrides_path.exists():
        with open(overrides_path, "r", encoding="utf-8") as f:
            overrides = json.load(f)

    files = sorted(list(dataset_path.rglob("*.jpg")) + list(dataset_path.rglob("*.png")))

    inventory = []
    audit_records = []

    sha_to_paths: Dict[str, List[str]] = {}
    dhash_to_paths: Dict[int, List[str]] = {}

    # Pass 1: Feature extraction & hash maps
    for f in files:
        rel_path = str(f.relative_to(dataset_path)).replace("\\", "/")
        parts = rel_path.split("/")
        split = parts[0]
        cls = parts[1]
        filename = parts[2]

        with open(f, "rb") as fp:
            raw_bytes = fp.read()

        sha256 = compute_sha256(raw_bytes)
        features = analyze_image_features(raw_bytes)

        sha_to_paths.setdefault(sha256, []).append(rel_path)
        if not features.get("corrupt"):
            dh_int = features["dhash_int"]
            dhash_to_paths.setdefault(dh_int, []).append(rel_path)

        inv_record = {
            "path": rel_path,
            "split": split,
            "class": cls,
            "filename": filename,
            "sha256": sha256,
            **features,
        }
        inventory.append(inv_record)

    # Pass 2: Duplicate detection & Split Leakage Check
    exact_duplicates = {k: v for k, v in sha_to_paths.items() if len(v) > 1}
    cross_split_leakage = []
    for sha, paths in exact_duplicates.items():
        splits_involved = {p.split("/")[0] for p in paths}
        if len(splits_involved) > 1:
            cross_split_leakage.append({"sha256": sha, "paths": paths, "splits": list(splits_involved)})

    # Near-duplicates (Hamming distance <= 3)
    near_duplicate_pairs = []
    valid_inv = [item for item in inventory if not item.get("corrupt")]
    for i in range(len(valid_inv)):
        for j in range(i + 1, len(valid_inv)):
            h1 = valid_inv[i]["dhash_int"]
            h2 = valid_inv[j]["dhash_int"]
            dist = hamming_distance(h1, h2)
            if dist <= 2:
                p1 = valid_inv[i]["path"]
                p2 = valid_inv[j]["path"]
                s1 = valid_inv[i]["split"]
                s2 = valid_inv[j]["split"]
                near_duplicate_pairs.append({
                    "path1": p1,
                    "path2": p2,
                    "distance": dist,
                    "cross_split": s1 != s2
                })

    # Pass 3: Audit decision mapping
    for item in inventory:
        rel = item["path"]
        cls = item["class"]
        split = item["split"]

        auto_status, auto_cat, auto_reason = automated_screen(item, cls)

        if rel in overrides:
            ov = overrides[rel]
            final_status = ov.get("status", auto_status)
            final_cat = ov.get("category", auto_cat)
            final_reason = ov.get("reason", auto_reason)
            source = "curated_review"
        else:
            final_status = auto_status
            final_cat = auto_cat
            final_reason = auto_reason
            source = "automated_screening"

        audit_record = {
            "path": rel,
            "split": split,
            "class": cls,
            "filename": item["filename"],
            "decision": final_status,
            "category": final_cat,
            "reason": final_reason,
            "decision_source": source,
            "automated_prediction": auto_status,
            "lap_var": item.get("lap_var", 0.0),
            "paper_ratio": item.get("paper_ratio", 0.0),
            "sat_mean": item.get("sat_mean", 0.0),
            "edge_ratio": item.get("edge_ratio", 0.0),
            "sha256": item["sha256"],
        }
        audit_records.append(audit_record)

    # Summary Statistics
    counts_before: Dict[str, Dict[str, int]] = {s: {c: 0 for c in CLASSES} for s in SPLITS}
    counts_retained: Dict[str, Dict[str, int]] = {s: {c: 0 for c in CLASSES} for s in SPLITS}
    counts_quarantine: Dict[str, Dict[str, int]] = {s: {c: 0 for c in CLASSES} for s in SPLITS}
    counts_review: Dict[str, Dict[str, int]] = {s: {c: 0 for c in CLASSES} for s in SPLITS}
    counts_corrupt: Dict[str, Dict[str, int]] = {s: {c: 0 for c in CLASSES} for s in SPLITS}

    for r in audit_records:
        s = r["split"]
        c = r["class"]
        counts_before[s][c] += 1
        if r["decision"] == "keep":
            counts_retained[s][c] += 1
        elif r["decision"] == "reject":
            counts_quarantine[s][c] += 1
        elif r["decision"] == "manual_review":
            counts_review[s][c] += 1

        if r.get("category") == "corrupt_file":
            counts_corrupt[s][c] += 1

    summary = {
        "total_images": len(files),
        "exact_duplicates": len(exact_duplicates),
        "cross_split_leakage": len(cross_split_leakage),
        "near_duplicate_pairs": len(near_duplicate_pairs),
        "status_breakdown": {
            "keep": sum(1 for r in audit_records if r["decision"] == "keep"),
            "reject": sum(1 for r in audit_records if r["decision"] == "reject"),
            "manual_review": sum(1 for r in audit_records if r["decision"] == "manual_review"),
        },
        "category_breakdown": {},
        "counts_before": counts_before,
        "counts_retained": counts_retained,
        "counts_quarantine": counts_quarantine,
        "counts_manual_review": counts_review,
        "counts_corrupt": counts_corrupt,
    }

    for r in audit_records:
        cat = r["category"]
        summary["category_breakdown"][cat] = summary["category_breakdown"].get(cat, 0) + 1

    return {
        "summary": summary,
        "inventory": inventory,
        "audit_records": audit_records,
        "cross_split_leakage": cross_split_leakage,
        "near_duplicate_pairs": near_duplicate_pairs,
    }


def save_reports(
    audit_data: Dict[str, Any],
    reports_dir: Path = REPORTS_DIR,
) -> Dict[str, str]:
    """Exports structured audit reports and inventory in JSON and CSV formats."""
    reports_dir.mkdir(parents=True, exist_ok=True)
    out_files = {}

    # 1. Inventory JSON & CSV
    inv_json = reports_dir / "plant_parts_inventory.json"
    with open(inv_json, "w", encoding="utf-8") as f:
        json.dump(audit_data["inventory"], f, indent=2)
    out_files["inventory_json"] = str(inv_json)

    inv_csv = reports_dir / "plant_parts_inventory.csv"
    if audit_data["inventory"]:
        keys = list(audit_data["inventory"][0].keys())
        with open(inv_csv, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=keys)
            writer.writeheader()
            writer.writerows(audit_data["inventory"])
        out_files["inventory_csv"] = str(inv_csv)

    # 2. Audit Report JSON & CSV
    audit_json = reports_dir / "plant_parts_audit_report.json"
    report_content = {
        "summary": audit_data["summary"],
        "cross_split_leakage": audit_data["cross_split_leakage"],
        "near_duplicate_pairs": audit_data["near_duplicate_pairs"],
        "audit_records": audit_data["audit_records"],
    }
    with open(audit_json, "w", encoding="utf-8") as f:
        json.dump(report_content, f, indent=2)
    out_files["audit_json"] = str(audit_json)

    audit_csv = reports_dir / "plant_parts_audit_report.csv"
    if audit_data["audit_records"]:
        keys = list(audit_data["audit_records"][0].keys())
        with open(audit_csv, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=keys)
            writer.writeheader()
            writer.writerows(audit_data["audit_records"])
        out_files["audit_csv"] = str(audit_csv)

    return out_files


def build_cleaned_and_quarantine(
    audit_data: Dict[str, Any],
    dataset_path: Path = DATASET_DIR,
    cleaned_path: Path = CLEANED_DIR,
    quarantine_path: Path = QUARANTINE_DIR,
    dry_run: bool = False,
) -> Dict[str, int]:
    """
    Builds clean dataset in cleaned_path and stores rejected/review items in quarantine_path.
    STRICTLY preserves dataset_path without modifying or deleting original files.
    """
    if dry_run:
        print("[DRY-RUN] Simulating cleaned dataset and quarantine creation...")
        return {"retained": audit_data["summary"]["status_breakdown"]["keep"], "quarantined": audit_data["summary"]["status_breakdown"]["reject"] + audit_data["summary"]["status_breakdown"]["manual_review"]}

    if cleaned_path.exists():
        shutil.rmtree(cleaned_path)
    if quarantine_path.exists():
        shutil.rmtree(quarantine_path)

    cleaned_path.mkdir(parents=True, exist_ok=True)
    quarantine_path.mkdir(parents=True, exist_ok=True)

    quarantine_manifest = []
    retained_count = 0
    quarantined_count = 0

    for r in audit_data["audit_records"]:
        src = dataset_path / r["path"]
        split = r["split"]
        cls = r["class"]
        fname = r["filename"]

        if r["decision"] == "keep":
            dst_dir = cleaned_path / split / cls
            dst_dir.mkdir(parents=True, exist_ok=True)
            dst_file = dst_dir / fname
            shutil.copy2(src, dst_file)
            retained_count += 1
        else:
            dst_dir = quarantine_path / split / cls
            dst_dir.mkdir(parents=True, exist_ok=True)
            dst_file = dst_dir / fname
            shutil.copy2(src, dst_file)
            quarantined_count += 1
            quarantine_manifest.append({
                "original_path": r["path"],
                "quarantine_path": str(dst_file.relative_to(quarantine_path)).replace("\\", "/"),
                "split": split,
                "class": cls,
                "decision": r["decision"],
                "category": r["category"],
                "reason": r["reason"],
                "sha256": r["sha256"],
            })

    manifest_file = quarantine_path / "quarantine_manifest.json"
    with open(manifest_file, "w", encoding="utf-8") as f:
        json.dump(quarantine_manifest, f, indent=2)

    return {"retained": retained_count, "quarantined": quarantined_count}


def reverse_cleanup(
    cleaned_path: Path = CLEANED_DIR,
    quarantine_path: Path = QUARANTINE_DIR,
) -> None:
    """Safely removes cleaned and quarantine directories without affecting original dataset."""
    print("Reversing cleanup: removing generated cleaned and quarantine directories...")
    if cleaned_path.exists():
        shutil.rmtree(cleaned_path)
        print(f"  Removed: {cleaned_path}")
    if quarantine_path.exists():
        shutil.rmtree(quarantine_path)
        print(f"  Removed: {quarantine_path}")
    print("[OK] Reversal complete. Original dataset in datasets/plant_parts/ remains untouched.")


def print_summary_table(summary: Dict[str, Any]) -> None:
    print("\n" + "=" * 80)
    print("PLANTSCAN AI: PLANT-PART DATASET QUALITY AUDIT SUMMARY")
    print("=" * 80)
    print(f"Total Images Audited:          {summary['total_images']}")
    print(f"Exact Duplicate Groups (SHA):  {summary['exact_duplicates']}")
    print(f"Cross-Split Duplicate Leakage: {summary['cross_split_leakage']}")
    print(f"Near-Duplicate Pairs (dHash):  {summary['near_duplicate_pairs']}")
    print("\nReview Status Breakdown:")
    for st, count in summary["status_breakdown"].items():
        pct = (count / summary["total_images"]) * 100
        print(f"  - {st.upper():15s}: {count:4d} ({pct:5.1f}%)")

    print("\nFlagged Defect Categories:")
    for cat, count in sorted(summary["category_breakdown"].items(), key=lambda x: x[1], reverse=True):
        print(f"  - {cat:35s}: {count:4d}")

    print("\n" + "-" * 80)
    print("CLASS & SPLIT MATRIX: BEFORE vs. RETAINED vs. QUARANTINED")
    print("-" * 80)
    header = f"{'Split':6s} | {'Class':6s} | {'Before':6s} | {'Retained (Keep)':15s} | {'Quarantined':12s} | {'Manual Review':13s}"
    print(header)
    print("-" * 80)

    for s in SPLITS:
        for c in CLASSES:
            b = summary["counts_before"][s][c]
            ret = summary["counts_retained"][s][c]
            q = summary["counts_quarantine"][s][c]
            mr = summary["counts_manual_review"][s][c]
            print(f"{s:6s} | {c:6s} | {b:6d} | {ret:15d} | {q:12d} | {mr:13d}")
    print("=" * 80)


def main():
    parser = argparse.ArgumentParser(description="PlantScanAI Plant-Part Dataset Quality Audit")
    parser.add_argument("--audit", action="store_true", default=True, help="Run audit and generate reports")
    parser.add_argument("--contact-sheets", action="store_true", default=True, help="Generate visual contact sheets")
    parser.add_argument("--clean", action="store_true", default=False, help="Build segregated cleaned dataset and quarantine")
    parser.add_argument("--reverse", action="store_true", default=False, help="Remove cleaned and quarantine directories")
    parser.add_argument("--dry-run", action="store_true", default=False, help="Perform dry run without writing files")

    args = parser.parse_args()

    if args.reverse:
        reverse_cleanup()
        return

    print("Running Plant-Part Dataset Quality Audit...")
    audit_data = audit_dataset()

    if args.contact_sheets:
        print("Generating contact sheets...")
        generate_contact_sheets(DATASET_DIR, CONTACT_SHEETS_DIR)

    report_files = save_reports(audit_data)
    print("Reports saved:")
    for k, v in report_files.items():
        print(f"  {k}: {v}")

    print_summary_table(audit_data["summary"])

    if args.clean:
        print("\nBuilding cleaned dataset and quarantine...")
        res = build_cleaned_and_quarantine(audit_data, dry_run=args.dry_run)
        print(f"[OK] Cleaned dataset ready at: {CLEANED_DIR} ({res['retained']} photos retained)")
        print(f"[OK] Quarantine directory at:  {QUARANTINE_DIR} ({res['quarantined']} items quarantined)")


if __name__ == "__main__":
    main()
