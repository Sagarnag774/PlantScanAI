import csv
from collections import defaultdict
from pathlib import Path

INPUT = Path("datasets/reports/model/final_class_taxonomy.csv")

with INPUT.open("r", encoding="utf-8", newline="") as f:
    rows = list(csv.DictReader(f))

print("=" * 100)
print("PLANTSCAN AI - FINAL TAXONOMY AUDIT")
print("=" * 100)

groups = defaultdict(list)

for row in rows:
    groups[row["canonical_class"]].append(row)

print(f"\nInventory rows        : {len(rows)}")
print(f"Unique canonical     : {len(groups)}")

print("\n" + "=" * 100)
print("CANONICAL CLASSES WITH MULTIPLE SOURCE ROWS")
print("=" * 100)

for canonical in sorted(groups):
    items = groups[canonical]

    if len(items) > 1:
        print(f"\n{canonical}  [{len(items)} mappings]")

        for row in items:
            print(
                f"  {row['dataset']:12} | "
                f"{row['crop']:12} | "
                f"{row['raw_class']}"
            )

print("\n" + "=" * 100)
print("GENERIC / SUSPICIOUS CANONICAL CLASSES")
print("=" * 100)

for canonical in sorted(groups):
    if canonical in {"healthy", ""}:
        print(f"\n{canonical or '<EMPTY>'}")

        for row in groups[canonical]:
            print(
                f"  {row['dataset']:12} | "
                f"{row['crop']:12} | "
                f"{row['raw_class']}"
            )

print("\n" + "=" * 100)
print("CANONICAL CLASS COUNT BY CROP")
print("=" * 100)

crop_classes = defaultdict(set)

for row in rows:
    crop_classes[row["crop"]].add(row["canonical_class"])

for crop in sorted(crop_classes):
    print(f"{crop:15} : {len(crop_classes[crop])}")

print("\n" + "=" * 100)
print("END")
print("=" * 100)
