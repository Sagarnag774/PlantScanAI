import csv
from collections import defaultdict
from pathlib import Path

INPUT = Path("datasets/reports/model/final_class_taxonomy.csv")

with INPUT.open("r", encoding="utf-8", newline="") as f:
    rows = list(csv.DictReader(f))

print("=" * 100)
print("PLANTSCAN AI - TAXONOMY ANOMALY AUDIT")
print("=" * 100)

print("\n--- GENERIC HEALTHY MAPPING ---")

for row in rows:
    if row["canonical_class"] == "healthy":
        print(
            f"{row['dataset']:12} | "
            f"{row['crop']:12} | "
            f"{row['raw_class']:45} | "
            f"{row['image_count']}"
        )

print("\n--- BELL PEPPER CLASSES ---")

for row in rows:
    if row["crop"].lower() == "bell pepper":
        print(
            f"{row['dataset']:12} | "
            f"{row['raw_class']:45} | "
            f"{row['canonical_class']:40} | "
            f"{row['category']}"
        )

print("\n--- ALL PLANTVILLAGE MAPPINGS ---")

for row in rows:
    if row["dataset"] == "PlantVillage":
        print(
            f"{row['raw_class']:60} -> "
            f"{row['canonical_class']}"
        )

print("\n--- CANONICAL CLASS COUNTS BY CROP ---")

groups = defaultdict(set)

for row in rows:
    groups[row["crop"]].add(row["canonical_class"])

for crop in sorted(groups):
    print(
        f"{crop:15} : "
        f"{len(groups[crop])} classes"
    )
    for cls in sorted(groups[crop]):
        print(f"    {cls}")

print("\n" + "=" * 100)
print("END")
print("=" * 100)