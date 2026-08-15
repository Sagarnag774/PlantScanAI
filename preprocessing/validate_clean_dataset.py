from pathlib import Path
import csv
import hashlib
from collections import Counter, defaultdict
from PIL import Image


PROJECT_ROOT = Path(__file__).resolve().parents[1]

DATASET_DIR = (
    PROJECT_ROOT
    / "datasets"
    / "processed"
    / "cleaned_raw"
)

AUDIT_FILE = (
    PROJECT_ROOT
    / "datasets"
    / "reports"
    / "duplicate_audit.csv"
)

REPORT_FILE = (
    PROJECT_ROOT
    / "datasets"
    / "reports"
    / "final_dataset_validation.csv"
)

IMAGE_EXTENSIONS = {
    ".jpg",
    ".jpeg",
    ".png",
    ".bmp",
    ".webp",
    ".tif",
    ".tiff",
}


def sha256(path):
    h = hashlib.sha256()

    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)

    return h.hexdigest()


def get_images(root):
    return [
        p
        for p in root.rglob("*")
        if p.is_file()
        and p.suffix.lower() in IMAGE_EXTENSIONS
    ]


def get_split(path):
    parts = {p.lower() for p in path.parts}

    if "test" in parts:
        return "test"

    if "train" in parts:
        return "train"

    if "validation" in parts or "val" in parts:
        return "validation"

    return "raw"


def get_dataset(path):
    parts = [p.lower() for p in path.parts]

    mapping = {
        "banana": "Banana",
        "cotton": "Cotton",
        "mango": "Mango",
        "plantdoc": "PlantDoc",
        "plantvillage": "PlantVillage",
        "rice": "Rice",
    }

    for part in parts:
        if part in mapping:
            return mapping[part]

    return "Unknown"


def get_label(path):
    return path.parent.name


def main():

    print("=" * 70)
    print("PlantScan AI - Final Clean Dataset Validation")
    print("=" * 70)

    if not DATASET_DIR.exists():
        print(f"\nERROR: Dataset not found:\n{DATASET_DIR}")
        return

    images = get_images(DATASET_DIR)

    print(f"\nImages found : {len(images):,}")

    # --------------------------------------------------------
    # 1. Image integrity
    # --------------------------------------------------------

    corrupt = []
    dimensions = Counter()

    print("\nChecking image integrity...")

    for index, path in enumerate(images, start=1):

        try:

            with Image.open(path) as image:
                image.verify()

            with Image.open(path) as image:
                dimensions[image.size] += 1

        except Exception as error:

            corrupt.append(
                {
                    "file": str(path.relative_to(PROJECT_ROOT)),
                    "error": str(error),
                }
            )

        if index % 5000 == 0:
            print(f"Checked {index:,}/{len(images):,}")

    print(f"Corrupt images : {len(corrupt):,}")

    # --------------------------------------------------------
    # 2. SHA-256 duplicate check
    # --------------------------------------------------------

    print("\nCalculating SHA-256 hashes...")

    hashes = defaultdict(list)

    for index, path in enumerate(images, start=1):

        digest = sha256(path)
        hashes[digest].append(path)

        if index % 5000 == 0:
            print(f"Hashed {index:,}/{len(images):,}")

    duplicate_groups = {
        digest: paths
        for digest, paths in hashes.items()
        if len(paths) > 1
    }

    duplicate_files = sum(
        len(paths)
        for paths in duplicate_groups.values()
    )

    print(
        f"\nExact duplicate groups : "
        f"{len(duplicate_groups):,}"
    )

    print(
        f"Files involved         : "
        f"{duplicate_files:,}"
    )

    # --------------------------------------------------------
    # 3. Train/test leakage
    # --------------------------------------------------------

    leakage_groups = []

    for digest, paths in duplicate_groups.items():

        splits = {
            get_split(path)
            for path in paths
        }

        if "train" in splits and "test" in splits:

            leakage_groups.append(
                (digest, paths)
            )

    print(
        f"Train/test duplicate groups : "
        f"{len(leakage_groups):,}"
    )

    # --------------------------------------------------------
    # 4. Dataset distribution
    # --------------------------------------------------------

    dataset_counts = Counter()
    split_counts = Counter()
    class_counts = Counter()

    for path in images:

        dataset = get_dataset(path)
        split = get_split(path)
        label = get_label(path)

        dataset_counts[dataset] += 1
        split_counts[split] += 1

        class_counts[
            (dataset, split, label)
        ] += 1

    print("\n--- Dataset Counts ---")

    for dataset, count in sorted(
        dataset_counts.items()
    ):
        print(
            f"{dataset:15} {count:,}"
        )

    print("\n--- Split Counts ---")

    for split, count in sorted(
        split_counts.items()
    ):
        print(
            f"{split:15} {count:,}"
        )

    # --------------------------------------------------------
    # 5. Compare against audit exclusions
    # --------------------------------------------------------

    excluded_paths = set()

    if AUDIT_FILE.exists():

        with open(
            AUDIT_FILE,
            "r",
            encoding="utf-8",
        ) as file:

            reader = csv.DictReader(file)

            for row in reader:

                if row["decision"] in {
                    "EXCLUDE",
                    "EXCLUDE_ALL",
                }:

                    excluded_paths.add(
                        row["file"].replace("\\", "/")
                    )

    remaining_excluded = []

    dataset_relative_paths = {
        path.relative_to(PROJECT_ROOT)
        .as_posix()
        for path in images
    }

    for excluded in excluded_paths:

        expected_prefix = "datasets/raw/"

        if not excluded.startswith(
            expected_prefix
        ):
            continue

        raw_relative = excluded[
            len(expected_prefix):
        ]

        cleaned_relative = (
            "datasets/processed/cleaned_raw/"
            + raw_relative
        )

        if cleaned_relative in dataset_relative_paths:

            remaining_excluded.append(
                excluded
            )

    print(
        "\nAudit exclusions still present : "
        f"{len(remaining_excluded):,}"
    )

    # --------------------------------------------------------
    # 6. Final status
    # --------------------------------------------------------

    passed = (
        len(corrupt) == 0
        and len(leakage_groups) == 0
        and len(remaining_excluded) == 0
    )

    print("\n" + "=" * 70)
    print("FINAL VALIDATION RESULT")
    print("=" * 70)

    if passed:

        print("\nSTATUS: PASS")
        print("\nDataset is ready to be frozen as Dataset v1.")

    else:

        print("\nSTATUS: FAIL")

        if corrupt:
            print(
                f"- Corrupt images: {len(corrupt)}"
            )

        if leakage_groups:
            print(
                f"- Train/test duplicate groups: "
                f"{len(leakage_groups)}"
            )

        if remaining_excluded:
            print(
                f"- Audit exclusions still present: "
                f"{len(remaining_excluded)}"
            )

    # --------------------------------------------------------
    # 7. Save summary report
    # --------------------------------------------------------

    REPORT_FILE.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    with open(
        REPORT_FILE,
        "w",
        newline="",
        encoding="utf-8",
    ) as file:

        writer = csv.writer(file)

        writer.writerow(
            ["metric", "value"]
        )

        writer.writerow(
            ["total_images", len(images)]
        )

        writer.writerow(
            ["corrupt_images", len(corrupt)]
        )

        writer.writerow(
            [
                "exact_duplicate_groups",
                len(duplicate_groups),
            ]
        )

        writer.writerow(
            [
                "exact_duplicate_files",
                duplicate_files,
            ]
        )

        writer.writerow(
            [
                "train_test_duplicate_groups",
                len(leakage_groups),
            ]
        )

        writer.writerow(
            [
                "audit_exclusions_still_present",
                len(remaining_excluded),
            ]
        )

        writer.writerow(
            [
                "validation_status",
                "PASS" if passed else "FAIL",
            ]
        )

    print(
        f"\nValidation report:"
        f"\n{REPORT_FILE}"
    )


if __name__ == "__main__":
    main()