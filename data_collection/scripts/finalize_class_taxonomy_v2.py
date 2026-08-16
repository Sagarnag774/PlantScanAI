import csv
from pathlib import Path

INPUT = Path("datasets/reports/model/final_class_taxonomy.csv")
OUTPUT = Path("datasets/reports/model/final_class_taxonomy_v2.csv")

HEALTHY_FIXES = {
    ("Banana", "healthy"): "banana_healthy",
    ("Cotton", "healthy"): "cotton_healthy",
    ("Mango", "Healthy"): "mango_healthy",
}


def main():
    if not INPUT.exists():
        raise FileNotFoundError(INPUT)

    with INPUT.open("r", encoding="utf-8", newline="") as f:
        rows = list(csv.DictReader(f))

    for row in rows:
        key = (
            row["dataset"],
            row["raw_class"],
        )

        if key in HEALTHY_FIXES:
            row["canonical_class"] = HEALTHY_FIXES[key]
            row["crop"] = row["crop"]
            row["category"] = "healthy"
            row["decision"] = "include"
            row["reason"] = (
                "Corrected to crop-specific healthy canonical class."
            )

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

    with OUTPUT.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)

    print("=" * 70)
    print("PlantScan AI - Taxonomy v2")
    print("=" * 70)
    print(f"Input rows  : {len(rows)}")
    print(f"Output      : {OUTPUT}")
    print()
    print("Corrections:")
    print("  Banana healthy -> banana_healthy")
    print("  Cotton healthy -> cotton_healthy")
    print("  Mango Healthy  -> mango_healthy")
    print()
    print("No images were modified.")
    print("No images were deleted.")


if __name__ == "__main__":
    main()