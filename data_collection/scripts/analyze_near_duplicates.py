from pathlib import Path
import csv
from collections import defaultdict


# ============================================================
# PlantScan AI - Near Duplicate Analysis
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parents[2]

REPORT_DIR = PROJECT_ROOT / "datasets" / "reports"

INPUT_FILE = REPORT_DIR / "near_duplicate_images.csv"

OUTPUT_FILE = REPORT_DIR / "near_duplicate_analysis.csv"


# ============================================================
# Helpers
# ============================================================

def normalize_path(path_string):
    return Path(path_string)


def get_crop_from_path(path):
    parts = path.parts

    try:
        raw_index = parts.index("raw")

        if raw_index + 1 < len(parts):
            return parts[raw_index + 1]

    except ValueError:
        pass

    return "unknown"


def get_dataset_type(path):
    path_string = str(path).lower()

    if "augmentedset" in path_string:
        return "augmented"

    if "originalset" in path_string:
        return "original"

    if "plantvillage" in path_string:
        return "plantvillage"

    if "plantdoc" in path_string:
        return "plantdoc"

    return "other"


# ============================================================
# Main
# ============================================================

def analyze():

    print("=" * 70)
    print("PlantScan AI - Near Duplicate Analysis")
    print("=" * 70)

    if not INPUT_FILE.exists():

        print(
            f"\nERROR: Report not found:\n"
            f"{INPUT_FILE}"
        )

        return

    pairs = []

    with open(
        INPUT_FILE,
        "r",
        encoding="utf-8",
    ) as file:

        reader = csv.DictReader(file)

        for row in reader:

            pairs.append(
                {
                    "distance": int(
                        row["distance"]
                    ),
                    "image_a": Path(
                        row["image_a"]
                    ),
                    "image_b": Path(
                        row["image_b"]
                    ),
                }
            )

    print(
        f"\nCandidate pairs : "
        f"{len(pairs):,}"
    )

    # --------------------------------------------------------
    # Unique images
    # --------------------------------------------------------

    unique_images = set()

    for pair in pairs:

        unique_images.add(
            str(pair["image_a"])
        )

        unique_images.add(
            str(pair["image_b"])
        )

    print(
        f"Unique images involved : "
        f"{len(unique_images):,}"
    )

    # --------------------------------------------------------
    # Distance statistics
    # --------------------------------------------------------

    distance_counts = defaultdict(int)

    for pair in pairs:

        distance_counts[
            pair["distance"]
        ] += 1

    print("\n--- Distance Summary ---")

    for distance in sorted(
        distance_counts
    ):

        print(
            f"Distance {distance}: "
            f"{distance_counts[distance]:,} pairs"
        )

    # --------------------------------------------------------
    # Crop statistics
    # --------------------------------------------------------

    crop_counts = defaultdict(int)

    for pair in pairs:

        crop_a = get_crop_from_path(
            pair["image_a"]
        )

        crop_b = get_crop_from_path(
            pair["image_b"]
        )

        crop_counts[crop_a] += 1

        if crop_b != crop_a:
            crop_counts[crop_b] += 1

    print("\n--- Crops Involved ---")

    for crop, count in sorted(
        crop_counts.items(),
        key=lambda item: item[1],
        reverse=True,
    ):

        print(
            f"{crop:20s} "
            f"{count:,}"
        )

    # --------------------------------------------------------
    # Dataset type statistics
    # --------------------------------------------------------

    dataset_counts = defaultdict(int)

    for pair in pairs:

        type_a = get_dataset_type(
            pair["image_a"]
        )

        type_b = get_dataset_type(
            pair["image_b"]
        )

        dataset_counts[
            f"{type_a} <-> {type_b}"
        ] += 1

    print("\n--- Dataset Relationships ---")

    for relationship, count in sorted(
        dataset_counts.items(),
        key=lambda item: item[1],
        reverse=True,
    ):

        print(
            f"{relationship:35s} "
            f"{count:,}"
        )

    # --------------------------------------------------------
    # Distance 0 analysis
    # --------------------------------------------------------

    exact_perceptual = [
        pair
        for pair in pairs
        if pair["distance"] == 0
    ]

    print(
        "\n--- Distance 0 Analysis ---"
    )

    print(
        f"Distance 0 pairs : "
        f"{len(exact_perceptual):,}"
    )

    distance_zero_images = set()

    for pair in exact_perceptual:

        distance_zero_images.add(
            str(pair["image_a"])
        )

        distance_zero_images.add(
            str(pair["image_b"])
        )

    print(
        f"Unique images involved : "
        f"{len(distance_zero_images):,}"
    )

    # --------------------------------------------------------
    # Augmented vs original
    # --------------------------------------------------------

    augmented_original = []

    for pair in exact_perceptual:

        type_a = get_dataset_type(
            pair["image_a"]
        )

        type_b = get_dataset_type(
            pair["image_b"]
        )

        if (
            (
                type_a == "augmented"
                and type_b == "original"
            )
            or
            (
                type_a == "original"
                and type_b == "augmented"
            )
        ):

            augmented_original.append(
                pair
            )

    print(
        "\n--- Augmented vs Original ---"
    )

    print(
        f"Distance 0 augmented/original pairs : "
        f"{len(augmented_original):,}"
    )

    # --------------------------------------------------------
    # Create detailed report
    # --------------------------------------------------------

    rows = []

    for pair in pairs:

        image_a = pair["image_a"]
        image_b = pair["image_b"]

        rows.append(
            {
                "distance": pair["distance"],
                "image_a": str(image_a),
                "image_b": str(image_b),
                "crop_a": get_crop_from_path(
                    image_a
                ),
                "crop_b": get_crop_from_path(
                    image_b
                ),
                "dataset_a": get_dataset_type(
                    image_a
                ),
                "dataset_b": get_dataset_type(
                    image_b
                ),
                "review_priority": (
                    "HIGH"
                    if pair["distance"] == 0
                    else
                    "MEDIUM"
                    if pair["distance"] <= 2
                    else
                    "LOW"
                ),
            }
        )

    with open(
        OUTPUT_FILE,
        "w",
        newline="",
        encoding="utf-8",
    ) as file:

        fieldnames = [
            "distance",
            "image_a",
            "image_b",
            "crop_a",
            "crop_b",
            "dataset_a",
            "dataset_b",
            "review_priority",
        ]

        writer = csv.DictWriter(
            file,
            fieldnames=fieldnames,
        )

        writer.writeheader()

        writer.writerows(rows)

    # --------------------------------------------------------
    # Final output
    # --------------------------------------------------------

    print(
        "\n--- Report ---"
    )

    print(
        OUTPUT_FILE
    )

    print(
        "\nAnalysis completed."
    )

    print("=" * 70)


# ============================================================
# Entry point
# ============================================================

if __name__ == "__main__":
    analyze()