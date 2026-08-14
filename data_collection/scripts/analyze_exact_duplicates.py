from pathlib import Path
import csv
from collections import defaultdict


# ============================================================
# PlantScan AI - Analyze Exact Duplicate Groups
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parents[2]

INPUT_FILE = (
    PROJECT_ROOT
    / "datasets"
    / "reports"
    / "near_duplicate_verified.csv"
)

OUTPUT_FILE = (
    PROJECT_ROOT
    / "datasets"
    / "reports"
    / "exact_duplicate_groups.csv"
)


# ============================================================
# Helpers
# ============================================================

def normalize_path(path):
    return path.replace("\\", "/")


def get_split(path):
    parts = [p.lower() for p in Path(path).parts]

    for split in ("train", "validation", "val", "test"):
        if split in parts:
            return "validation" if split == "val" else split

    return "raw"


def get_label(path):
    parts = list(Path(path).parts)

    # Find the dataset/source directory.
    dataset_index = None

    for i, part in enumerate(parts):
        if part.lower() in {
            "plantvillage",
            "plantdoc",
            "banana",
            "cotton",
            "mango",
            "rice",
        }:
            dataset_index = i
            break

    if dataset_index is None:
        return "Unknown"

    # For PlantVillage and PlantDoc:
    # raw/PlantDoc/test/<class>/image.jpg
    # raw/PlantVillage/<class>/image.jpg
    dataset = parts[dataset_index].lower()

    if dataset in {"plantdoc", "plantvillage"}:

        # Find the split directory after the dataset.
        start = dataset_index + 1

        if start < len(parts):
            if parts[start].lower() in {
                "train",
                "test",
                "validation",
                "val",
            }:
                start += 1

        if start < len(parts) - 1:
            return parts[start]

        return "Unknown"

    # Banana/Cotton/Mango/Rice:
    # use the directory immediately before the image,
    # except for AugmentedSet / OriginalSet.
    start = dataset_index + 1

    if start < len(parts):
        if parts[start].lower() in {
            "augmentedset",
            "originalset",
        }:
            start += 1

    if start < len(parts) - 1:
        return parts[start]

    return "Unknown"


def get_dataset(path):
    parts = [p.lower() for p in Path(path).parts]

    known = {
        "banana": "Banana",
        "cotton": "Cotton",
        "mango": "Mango",
        "rice": "Rice",
        "plantdoc": "PlantDoc",
        "plantvillage": "PlantVillage",
    }

    for part in parts:
        if part in known:
            return known[part]

    return "Unknown"


def get_subset(path):
    parts = [p.lower() for p in Path(path).parts]

    if "augmentedset" in parts:
        return "Augmented"

    if "originalset" in parts:
        return "Original"

    return "Main"


# ============================================================
# Main
# ============================================================

def main():

    print("=" * 70)
    print("PlantScan AI - Analyze Exact Duplicate Groups")
    print("=" * 70)

    if not INPUT_FILE.exists():
        print(f"\nERROR: Report not found:\n{INPUT_FILE}")
        return

    # --------------------------------------------------------
    # Read exact duplicate pairs
    # --------------------------------------------------------

    exact_pairs = []

    with open(
        INPUT_FILE,
        "r",
        encoding="utf-8",
    ) as file:

        reader = csv.DictReader(file)

        for row in reader:

            if row["exact_duplicate"] == "YES":
                exact_pairs.append(row)

    print(
        f"\nExact duplicate pairs : "
        f"{len(exact_pairs):,}"
    )

    # --------------------------------------------------------
    # Build connected duplicate groups
    # --------------------------------------------------------

    parent = {}
    all_paths = set()


    def find(x):

        if parent[x] != x:
            parent[x] = find(parent[x])

        return parent[x]


    def union(a, b):

        if a not in parent:
            parent[a] = a

        if b not in parent:
            parent[b] = b

        root_a = find(a)
        root_b = find(b)

        if root_a != root_b:
            parent[root_b] = root_a


    for row in exact_pairs:

        image_a = normalize_path(row["image_a"])
        image_b = normalize_path(row["image_b"])

        all_paths.add(image_a)
        all_paths.add(image_b)

        union(image_a, image_b)


    # --------------------------------------------------------
    # Group paths
    # --------------------------------------------------------

    groups = defaultdict(list)

    for path in all_paths:
        groups[find(path)].append(path)

    groups = list(groups.values())

    # Sort largest groups first
    groups.sort(
        key=len,
        reverse=True,
    )

    print(
        f"Unique files involved : "
        f"{len(all_paths):,}"
    )

    print(
        f"Duplicate groups      : "
        f"{len(groups):,}"
    )

    redundant_files = sum(
        len(group) - 1
        for group in groups
    )

    print(
        f"Potential redundant files : "
        f"{redundant_files:,}"
    )

    # --------------------------------------------------------
    # Analyze groups
    # --------------------------------------------------------

    report_rows = []

    split_leakage_groups = 0
    label_conflict_groups = 0
    cross_dataset_groups = 0

    for group_id, group in enumerate(
        groups,
        start=1,
    ):

        datasets = sorted({
            get_dataset(path)
            for path in group
        })

        subsets = sorted({
            get_subset(path)
            for path in group
        })

        splits = sorted({
            get_split(path)
            for path in group
        })

        labels = sorted({
            get_label(path)
            for path in group
        })

        split_leakage = (
            len(set(splits) - {"raw"}) > 1
        )

        label_conflict = (
            len(labels) > 1
        )

        cross_dataset = (
            len(datasets) > 1
        )

        if split_leakage:
            split_leakage_groups += 1

        if label_conflict:
            label_conflict_groups += 1

        if cross_dataset:
            cross_dataset_groups += 1

        report_rows.append(
            {
                "group_id": group_id,
                "group_size": len(group),
                "redundant_files": len(group) - 1,
                "datasets": "|".join(datasets),
                "subsets": "|".join(subsets),
                "splits": "|".join(splits),
                "labels": "|".join(labels),
                "split_leakage": (
                    "YES"
                    if split_leakage
                    else "NO"
                ),
                "label_conflict": (
                    "YES"
                    if label_conflict
                    else "NO"
                ),
                "cross_dataset": (
                    "YES"
                    if cross_dataset
                    else "NO"
                ),
                "files": " || ".join(
                    sorted(group)
                ),
            }
        )

    # --------------------------------------------------------
    # Save report
    # --------------------------------------------------------

    OUTPUT_FILE.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    fieldnames = [
        "group_id",
        "group_size",
        "redundant_files",
        "datasets",
        "subsets",
        "splits",
        "labels",
        "split_leakage",
        "label_conflict",
        "cross_dataset",
        "files",
    ]

    with open(
        OUTPUT_FILE,
        "w",
        newline="",
        encoding="utf-8",
    ) as file:

        writer = csv.DictWriter(
            file,
            fieldnames=fieldnames,
        )

        writer.writeheader()
        writer.writerows(report_rows)

    # --------------------------------------------------------
    # Summary
    # --------------------------------------------------------

    print("\n" + "=" * 70)
    print("EXACT DUPLICATE GROUP SUMMARY")
    print("=" * 70)

    print(
        f"\nExact duplicate pairs       : "
        f"{len(exact_pairs):,}"
    )

    print(
        f"Unique files involved       : "
        f"{len(all_paths):,}"
    )

    print(
        f"Duplicate groups            : "
        f"{len(groups):,}"
    )

    print(
        f"Potential redundant files   : "
        f"{redundant_files:,}"
    )

    print(
        f"\nGroups with split leakage   : "
        f"{split_leakage_groups:,}"
    )

    print(
        f"Groups with label conflicts : "
        f"{label_conflict_groups:,}"
    )

    print(
        f"Cross-dataset groups        : "
        f"{cross_dataset_groups:,}"
    )

    print(
        "\nLargest duplicate groups:"
    )

    for group in groups[:20]:

        print(
            f"  {len(group):>3} files"
        )

    print(
        "\n--- Report ---"
    )

    print(OUTPUT_FILE)

    print(
        "\nAnalysis completed."
    )

    print("=" * 70)


if __name__ == "__main__":
    main()