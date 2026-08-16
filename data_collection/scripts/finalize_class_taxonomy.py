import csv
from pathlib import Path

INPUT = Path("datasets/reports/model/class_taxonomy_review.csv")
OUTPUT = Path("datasets/reports/model/final_class_taxonomy.csv")

PLANTDOC_MAP = {
    "Apple Scab Leaf": ("Apple", "disease", "apple_scab"),
    "Apple leaf": ("Apple", "healthy", "apple_healthy"),
    "Apple rust leaf": ("Apple", "disease", "apple_rust"),

    "Bell_pepper leaf": ("Bell pepper", "healthy", "bell_pepper_healthy"),
    "Bell_pepper leaf spot": (
        "Bell pepper", "disease", "bell_pepper_leaf_spot"
    ),

    "Blueberry leaf": ("Blueberry", "healthy", "blueberry_healthy"),
    "Cherry leaf": ("Cherry", "healthy", "cherry_healthy"),

    "Corn Gray leaf spot": ("Maize", "disease", "maize_gray_leaf_spot"),
    "Corn leaf blight": ("Maize", "disease", "maize_leaf_blight"),
    "Corn rust leaf": ("Maize", "disease", "maize_rust"),

    "Peach leaf": ("Peach", "healthy", "peach_healthy"),

    "Potato leaf early blight": (
        "Potato", "disease", "potato_early_blight"
    ),
    "Potato leaf late blight": (
        "Potato", "disease", "potato_late_blight"
    ),

    "Raspberry leaf": ("Raspberry", "healthy", "raspberry_healthy"),
    "Soyabean leaf": ("Soybean", "healthy", "soybean_healthy"),

    "Squash Powdery mildew leaf": (
        "Squash", "disease", "squash_powdery_mildew"
    ),

    "Strawberry leaf": ("Strawberry", "healthy", "strawberry_healthy"),

    "Tomato Early blight leaf": (
        "Tomato", "disease", "tomato_early_blight"
    ),
    "Tomato Septoria leaf spot": (
        "Tomato", "disease", "tomato_septoria_leaf_spot"
    ),
    "Tomato leaf": ("Tomato", "healthy", "tomato_healthy"),
    "Tomato leaf bacterial spot": (
        "Tomato", "disease", "tomato_bacterial_spot"
    ),
    "Tomato leaf late blight": (
        "Tomato", "disease", "tomato_late_blight"
    ),
    "Tomato leaf mosaic virus": (
        "Tomato", "disease", "tomato_mosaic_virus"
    ),
    "Tomato leaf yellow virus": (
        "Tomato", "disease", "tomato_yellow_leaf_curl_virus"
    ),
    "Tomato mold leaf": (
        "Tomato", "disease", "tomato_leaf_mold"
    ),

    "grape leaf": ("Grape", "healthy", "grape_healthy"),
    "grape leaf black rot": (
        "Grape", "disease", "grape_black_rot"
    ),
}


def main():
    if not INPUT.exists():
        raise FileNotFoundError(INPUT)

    with INPUT.open("r", encoding="utf-8", newline="") as f:
        rows = list(csv.DictReader(f))

    output_rows = []

    for row in rows:
        dataset = row["dataset"]
        raw_class = row["raw_class"]

        if dataset == "PlantDoc":
            if raw_class not in PLANTDOC_MAP:
                raise ValueError(
                    f"Unmapped PlantDoc class: {raw_class}"
                )

            crop, category, canonical = PLANTDOC_MAP[raw_class]

            decision = "include"
            reason = "Verified PlantDoc class mapping."

        else:
            crop = row["crop"]
            category = row["category"]
            canonical = row["canonical_class"]
            decision = row["decision"]
            reason = row["reason"]

        output_rows.append({
            "dataset": dataset,
            "raw_class": raw_class,
            "image_count": row["image_count"],
            "crop": crop,
            "category": category,
            "canonical_class": canonical,
            "decision": decision,
            "reason": reason,
        })

    fields = [
        "dataset",
        "raw_class",
        "image_count",
        "crop",
        "category",
        "canonical_class",
        "decision",
        "reason",
    ]

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)

    with OUTPUT.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerows(output_rows)

    from collections import Counter

    print("=" * 70)
    print("PlantScan AI - Final Class Taxonomy")
    print("=" * 70)

    print(f"Inventory rows : {len(output_rows)}")

    print("\nCategories:")
    for k, v in sorted(
        Counter(r["category"] for r in output_rows).items()
    ):
        print(f"{k:12} : {v}")

    print("\nDecisions:")
    for k, v in sorted(
        Counter(r["decision"] for r in output_rows).items()
    ):
        print(f"{k:12} : {v}")

    print(f"\nReport:")
    print(OUTPUT)

    print("\nNo images were modified.")
    print("No images were deleted.")


if __name__ == "__main__":
    main()