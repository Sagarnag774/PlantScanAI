import csv
from pathlib import Path

INPUT = Path("datasets/reports/model/class_inventory.csv")
OUTPUT = Path("datasets/reports/model/class_taxonomy_review.csv")

DISEASE_TERMS = [
    "blight", "spot", "rust", "mildew", "mold", "mosaic", "virus",
    "curl", "bacterial", "anthracnose", "canker", "weevil", "midge",
    "die back", "dieback", "scald", "blast", "sheath", "pestalotiopsis",
    "cordana", "sigatoka", "fusarium", "fussarium", "spider_mites",
    "spider mite", "target spot", "powdery", "sooty"
]

HEALTHY_TERMS = ["healthy"]

GENERIC_LEAF_TERMS = [
    " leaf", "leaf", "leaves"
]

def infer_crop(dataset, raw_class):
    s = raw_class.lower()
    if dataset == "PlantVillage":
        if "tomato" in s:
            return "Tomato"
        if "potato" in s:
            return "Potato"
        if "pepper" in s:
            return "Bell pepper"
    if dataset == "PlantDoc":
        mapping = {
            "apple": "Apple",
            "bell_pepper": "Bell pepper",
            "blueberry": "Blueberry",
            "cherry": "Cherry",
            "corn": "Maize",
            "peach": "Peach",
            "potato": "Potato",
            "raspberry": "Raspberry",
            "soyabean": "Soybean",
            "squash": "Squash",
            "strawberry": "Strawberry",
            "tomato": "Tomato",
            "grape": "Grape",
        }
        for key, crop in mapping.items():
            if key in s:
                return crop
    return dataset if dataset in {
        "Banana", "Cotton", "Mango", "Rice"
    } else ""

def canonicalize(raw_class):
    s = raw_class.strip().lower()
    replacements = {
        "_": " ",
        "-": " ",
    }
    for a, b in replacements.items():
        s = s.replace(a, b)
    s = " ".join(s.split())

    # Explicit known mappings from the current inventory.
    explicit = {
        "fussarium wilt": "fusarium_wilt",
        "bacterial blight": "bacterial_leaf_blight",
        "brown spot": "brown_spot",
        "leaf blast": "leaf_blast",
        "leaf scald": "leaf_scald",
        "sheath blight": "sheath_blight",
        "anthracnose": "anthracnose",
        "bacterial canker": "bacterial_canker",
        "cutting weevil": "cutting_weevil",
        "die back": "die_back",
        "gall midge": "gall_midge",
        "powdery mildew": "powdery_mildew",
        "sooty mould": "sooty_mould",
        "pestalotiopsis": "pestalotiopsis",
        "cordana": "cordana",
        "sigatoka": "sigatoka",
        "bacterial blight": "bacterial_blight",
        "curl virus": "curl_virus",
    }
    if s in explicit:
        return explicit[s]

    # PlantVillage normalization.
    pv = {
        "pepper bell bacterial spot": "bell_pepper_bacterial_spot",
        "pepper bell healthy": "bell_pepper_healthy",
        "potato early blight": "potato_early_blight",
        "potato late blight": "potato_late_blight",
        "potato healthy": "potato_healthy",
        "tomato bacterial spot": "tomato_bacterial_spot",
        "tomato early blight": "tomato_early_blight",
        "tomato late blight": "tomato_late_blight",
        "tomato leaf mold": "tomato_leaf_mold",
        "tomato septoria leaf spot": "tomato_septoria_leaf_spot",
        "tomato spider mites two spotted spider mite": "tomato_spider_mites",
        "tomato target spot": "tomato_target_spot",
        "tomato tomato yellowleaf curl virus": "tomato_yellow_leaf_curl_virus",
        "tomato tomato mosaic virus": "tomato_mosaic_virus",
        "tomato healthy": "tomato_healthy",
    }
    if s in pv:
        return pv[s]

    return s.replace(" ", "_")

def classify(dataset, raw_class):
    s = raw_class.strip().lower()

    if s in HEALTHY_TERMS:
        return "healthy", canonicalize(raw_class), "include", "Explicit healthy class."

    if dataset == "PlantDoc":
        # Generic leaf classes are not automatically assumed to be healthy.
        disease_hit = any(term in s for term in DISEASE_TERMS)
        if disease_hit:
            return "disease", canonicalize(raw_class), "review", \
                "Disease-like PlantDoc label; canonical mapping requires manual approval."
        return "generic_leaf", "", "review", \
            "Generic PlantDoc leaf label; do not assume healthy or disease."

    if "healthy" in s:
        return "healthy", canonicalize(raw_class), "include", "Healthy label."

    if any(term in s for term in DISEASE_TERMS):
        return "disease", canonicalize(raw_class), "include", \
            "Disease label identified by explicit disease terminology."

    return "ambiguous", "", "review", \
        "No sufficiently reliable disease/healthy classification rule matched."

def main():
    if not INPUT.exists():
        raise FileNotFoundError(f"Missing input: {INPUT}")

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)

    with INPUT.open("r", encoding="utf-8", newline="") as f:
        rows = list(csv.DictReader(f))

    fields = [
        "dataset", "raw_class", "image_count", "crop",
        "category", "canonical_class", "decision", "reason"
    ]

    out_rows = []
    for row in rows:
        dataset = row["dataset"].strip()
        raw_class = row["class"].strip()
        category, canonical, decision, reason = classify(dataset, raw_class)

        out_rows.append({
            "dataset": dataset,
            "raw_class": raw_class,
            "image_count": row["image_count"],
            "crop": infer_crop(dataset, raw_class),
            "category": category,
            "canonical_class": canonical,
            "decision": decision,
            "reason": reason,
        })

    with OUTPUT.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerows(out_rows)

    from collections import Counter
    cats = Counter(r["category"] for r in out_rows)
    decisions = Counter(r["decision"] for r in out_rows)

    print("=" * 70)
    print("PlantScan AI - Build Class Taxonomy Review")
    print("=" * 70)
    print(f"Inventory rows : {len(out_rows)}")
    print()
    print("--- Categories ---")
    for k, v in sorted(cats.items()):
        print(f"{k:15} : {v}")
    print()
    print("--- Decisions ---")
    for k, v in sorted(decisions.items()):
        print(f"{k:15} : {v}")
    print()
    print(f"Report: {OUTPUT}")
    print()
    print("IMPORTANT:")
    print("- REVIEW rows require human approval.")
    print("- No dataset images were changed.")
    print("- No images were deleted.")
    print("- Do not train until the taxonomy is approved.")

if __name__ == "__main__":
    main()
