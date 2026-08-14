import csv
from collections import defaultdict

FILE = "datasets/reports/duplicate_audit.csv"

groups = defaultdict(list)

with open(FILE, "r", encoding="utf-8") as file:
    reader = csv.DictReader(file)

    for row in reader:
        groups[row["group_id"]].append(row)

print("=" * 70)
print("AUDIT DECISIONS")
print("=" * 70)

for group_id in sorted(groups, key=int):

    rows = groups[group_id]

    decisions = sorted(
        set(row["decision"] for row in rows)
    )

    if "EXCLUDE_ALL" in decisions:
        print(
            f"\nGROUP {group_id} | "
            f"DECISION={decisions}"
        )

        for row in rows:
            print(
                f"  {row['split']:12} | "
                f"{row['label']:35} | "
                f"{row['file']}"
            )