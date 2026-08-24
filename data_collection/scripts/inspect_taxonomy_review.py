import csv
from pathlib import Path

INPUT = Path("datasets/reports/model/class_taxonomy_review.csv")

with INPUT.open("r", encoding="utf-8", newline="") as f:
    rows = list(csv.DictReader(f))

print("=" * 100)
print("PLANTSCAN AI - ALL TAXONOMY REVIEW CLASSES")
print("=" * 100)

review_rows = [
    row for row in rows
    if row["decision"].strip().lower() == "review"
]

print(f"\nTotal review classes: {len(review_rows)}\n")

for i, row in enumerate(review_rows, 1):
    print("-" * 100)
    print(f"{i:02d}")
    print(f"Dataset         : {row['dataset']}")
    print(f"Crop            : {row['crop']}")
    print(f"Raw class       : {row['raw_class']}")
    print(f"Image count     : {row['image_count']}")
    print(f"Category        : {row['category']}")
    print(f"Canonical class : {row['canonical_class']}")
    print(f"Reason          : {row['reason']}")

print("\n" + "=" * 100)
print("END OF REVIEW CLASSES")
print("=" * 100)