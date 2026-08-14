from pathlib import Path
import csv


PROJECT_ROOT = Path(__file__).resolve().parents[2]

INPUT_FILE = (
    PROJECT_ROOT
    / "datasets/reports/exact_duplicate_groups.csv"
)

OUTPUT_FILE = (
    PROJECT_ROOT
    / "datasets/reports/duplicate_audit.csv"
)


# ============================================================
# MANUALLY REVIEWED GROUPS
# ============================================================

# Same exact image but conflicting labels.
# Both copies are excluded from the cleaned disease dataset.
CONFLICT_GROUPS = {
    "16",
    "50",
    "54",
    "68",
    "97",
    "155",
    "191",
    "197",
    "220",
    "226",
}


# Same exact image + same label in train/test.
# Keep TEST and exclude TRAIN.
LEAKAGE_GROUPS = {
    "205",
    "235",
    "239",
}


# ============================================================
# HELPERS
# ============================================================

def normalize_path(path):
    return path.replace("\\", "/")


def get_split(path):
    parts = [
        p.lower()
        for p in Path(path).parts
    ]

    if "test" in parts:
        return "test"

    if "train" in parts:
        return "train"

    if "validation" in parts or "val" in parts:
        return "validation"

    return "raw"


def get_dataset(path):
    parts = [
        p.lower()
        for p in Path(path).parts
    ]

    dataset_names = {
        "plantdoc": "PlantDoc",
        "plantvillage": "PlantVillage",
        "banana": "Banana",
        "cotton": "Cotton",
        "mango": "Mango",
        "rice": "Rice",
    }

    for part in parts:

        if part in dataset_names:
            return dataset_names[part]

    return "Unknown"


def get_label(path):
    """
    The directory immediately before the filename
    is the source label.

    Example:

    .../Potato leaf late blight/image.jpg

    -> Potato leaf late blight
    """

    return Path(path).parent.name


# ============================================================
# MAIN
# ============================================================

def main():

    print("=" * 70)
    print("PlantScan AI - Create Duplicate Audit")
    print("=" * 70)

    if not INPUT_FILE.exists():

        print(
            f"\nERROR: Input report not found:\n"
            f"{INPUT_FILE}"
        )

        return

    rows = []

    with open(
        INPUT_FILE,
        "r",
        encoding="utf-8",
    ) as file:

        reader = csv.DictReader(file)

        for row in reader:

            rows.append(row)

    print(
        f"\nExact duplicate pairs : "
        f"{len(rows):,}"
    )

    # --------------------------------------------------------
    # Counters
    # --------------------------------------------------------

    group_count = len(rows)

    total_files = 0

    keep_count = 0
    exclude_count = 0

    conflict_count = 0
    leakage_count = 0

    audit_rows = []

    # --------------------------------------------------------
    # Process each EXISTING group ID
    # --------------------------------------------------------

    for row in rows:

        group_id = row["group_id"]

        files = [
            normalize_path(f.strip())
            for f in row["files"].split(" || ")
            if f.strip()
        ]

        total_files += len(files)

        # ====================================================
        # CONFLICT GROUP
        # ====================================================

        if group_id in CONFLICT_GROUPS:

            conflict_count += 1

            reason = (
                "Exact duplicate with conflicting source "
                "labels. Manual review could not establish "
                "a sufficiently reliable label. Exclude "
                "from cleaned disease dataset."
            )

            for file_path in files:

                audit_rows.append(
                    {
                        "group_id": group_id,
                        "file": file_path,
                        "dataset": get_dataset(file_path),
                        "label": get_label(file_path),
                        "split": get_split(file_path),
                        "decision": "EXCLUDE_ALL",
                        "keep_file": "",
                        "exclude_file": file_path,
                        "reason": reason,
                    }
                )

                exclude_count += 1

            continue

        # ====================================================
        # TRAIN / TEST LEAKAGE
        # ====================================================

        if group_id in LEAKAGE_GROUPS:

            leakage_count += 1

            test_files = [
                f
                for f in files
                if get_split(f) == "test"
            ]

            train_files = [
                f
                for f in files
                if get_split(f) == "train"
            ]

            # We expect exactly one test and one train copy.
            if len(test_files) != 1 or len(train_files) != 1:

                print(
                    f"\nERROR: Unexpected split structure "
                    f"in leakage Group {group_id}"
                )

                print(
                    f"Files: {files}"
                )

                return

            keep_file = test_files[0]

            reason = (
                "Exact duplicate appears in both train "
                "and test with the same label. Keep the "
                "test copy and exclude the training copy "
                "to eliminate test-set leakage."
            )

            for file_path in files:

                if file_path == keep_file:

                    decision = "KEEP"
                    exclude_file = ""

                    keep_count += 1

                else:

                    decision = "EXCLUDE"
                    exclude_file = file_path

                    exclude_count += 1

                audit_rows.append(
                    {
                        "group_id": group_id,
                        "file": file_path,
                        "dataset": get_dataset(file_path),
                        "label": get_label(file_path),
                        "split": get_split(file_path),
                        "decision": decision,
                        "keep_file": keep_file,
                        "exclude_file": exclude_file,
                        "reason": reason,
                    }
                )

            continue

        # ====================================================
        # NORMAL EXACT DUPLICATE GROUP
        # ====================================================

        # Deterministic choice:
        # Keep the first path from the authoritative report.
        keep_file = files[0]

        reason = (
            "Exact duplicate within the dataset. "
            "Retain one deterministic copy and "
            "exclude redundant copies."
        )

        for index, file_path in enumerate(files):

            if index == 0:

                decision = "KEEP"
                exclude_file = ""

                keep_count += 1

            else:

                decision = "EXCLUDE"
                exclude_file = file_path

                exclude_count += 1

            audit_rows.append(
                {
                    "group_id": group_id,
                    "file": file_path,
                    "dataset": get_dataset(file_path),
                    "label": get_label(file_path),
                    "split": get_split(file_path),
                    "decision": decision,
                    "keep_file": keep_file,
                    "exclude_file": exclude_file,
                    "reason": reason,
                }
            )

    # --------------------------------------------------------
    # Write report
    # --------------------------------------------------------

    fieldnames = [
        "group_id",
        "file",
        "dataset",
        "label",
        "split",
        "decision",
        "keep_file",
        "exclude_file",
        "reason",
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
        writer.writerows(audit_rows)

    # --------------------------------------------------------
    # Summary
    # --------------------------------------------------------

    print("\n" + "=" * 70)
    print("AUDIT SUMMARY")
    print("=" * 70)

    print(
        f"\nExact duplicate groups : "
        f"{group_count:,}"
    )

    print(
        f"Files involved         : "
        f"{total_files:,}"
    )

    print(
        f"Files marked KEEP      : "
        f"{keep_count:,}"
    )

    print(
        f"Files marked EXCLUDE   : "
        f"{exclude_count:,}"
    )

    print(
        f"\nConflict groups        : "
        f"{conflict_count:,}"
    )

    print(
        f"Leakage groups         : "
        f"{leakage_count:,}"
    )

    print(
        f"\nReport:"
        f"\n{OUTPUT_FILE}"
    )

    print("\nNo files were deleted.")

    print("=" * 70)


if __name__ == "__main__":
    main()