from pathlib import Path
from collections import defaultdict, Counter
import csv
import json


# ============================================================
# PlantScan AI - Dataset Analyzer
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parents[2]

REPORT_DIR = PROJECT_ROOT / "datasets" / "reports"

INVENTORY_FILE = REPORT_DIR / "dataset_inventory.csv"

ANALYSIS_CSV = REPORT_DIR / "class_analysis.csv"
ANALYSIS_JSON = REPORT_DIR / "class_analysis.json"


# ============================================================
# Configuration
# ============================================================

# Minimum number of images we consider reasonable for
# a disease class during initial dataset selection.
MIN_CLASS_IMAGES = 100


# ============================================================
# Read inventory
# ============================================================

def load_inventory():

    if not INVENTORY_FILE.exists():

        raise FileNotFoundError(
            f"Inventory not found:\n{INVENTORY_FILE}\n\n"
            "Run validate_dataset.py first."
        )

    rows = []

    with open(
        INVENTORY_FILE,
        "r",
        encoding="utf-8",
    ) as file:

        reader = csv.DictReader(file)

        for row in reader:
            rows.append(row)

    return rows


# ============================================================
# Detect healthy classes
# ============================================================

def is_healthy_class(class_name):

    name = class_name.lower()

    healthy_keywords = {
        "healthy",
        "normal",
    }

    return any(
        keyword in name
        for keyword in healthy_keywords
    )


# ============================================================
# Analyze dataset
# ============================================================

def analyze_dataset():

    rows = load_inventory()

    # --------------------------------------------------------
    # Only use valid/warning images.
    # --------------------------------------------------------

    rows = [
        row
        for row in rows
        if row["status"] in {
            "valid",
            "warning",
        }
    ]

    # --------------------------------------------------------
    # Structure:
    #
    # crop -> source -> class -> count
    # --------------------------------------------------------

    class_counts = defaultdict(Counter)

    for row in rows:

        crop = row["crop"]
        source = row["source"]
        class_name = row["class"]

        class_counts[crop][
            f"{source}::{class_name}"
        ] += 1

    # --------------------------------------------------------
    # Crop statistics
    # --------------------------------------------------------

    crop_statistics = {}

    for crop, classes in class_counts.items():

        total_images = sum(
            classes.values()
        )

        healthy_images = sum(
            count
            for class_key, count in classes.items()
            if is_healthy_class(
                class_key.split(
                    "::",
                    maxsplit=1
                )[1]
            )
        )

        disease_images = (
            total_images - healthy_images
        )

        class_sizes = list(
            classes.values()
        )

        min_class = min(
            class_sizes
        )

        max_class = max(
            class_sizes
        )

        classes_above_threshold = sum(
            count >= MIN_CLASS_IMAGES
            for count in class_sizes
        )

        crop_statistics[crop] = {

            "total_images": total_images,

            "number_of_original_classes": len(
                classes
            ),

            "healthy_images": healthy_images,

            "disease_images": disease_images,

            "minimum_class_images": min_class,

            "maximum_class_images": max_class,

            "classes_with_at_least_100_images":
                classes_above_threshold,

            "classes": dict(
                sorted(
                    classes.items()
                )
            ),
        }

    # --------------------------------------------------------
    # Save CSV
    # --------------------------------------------------------

    with open(
        ANALYSIS_CSV,
        "w",
        newline="",
        encoding="utf-8",
    ) as file:

        fieldnames = [
            "crop",
            "source",
            "class",
            "images",
            "healthy",
            "meets_100_image_threshold",
        ]

        writer = csv.DictWriter(
            file,
            fieldnames=fieldnames,
        )

        writer.writeheader()

        for crop in sorted(
            class_counts
        ):

            for class_key, count in sorted(
                class_counts[crop].items()
            ):

                source, class_name = class_key.split(
                    "::",
                    maxsplit=1,
                )

                writer.writerow(
                    {
                        "crop": crop,
                        "source": source,
                        "class": class_name,
                        "images": count,
                        "healthy":
                            is_healthy_class(
                                class_name
                            ),
                        "meets_100_image_threshold":
                            count >= MIN_CLASS_IMAGES,
                    }
                )

    # --------------------------------------------------------
    # Save JSON
    # --------------------------------------------------------

    with open(
        ANALYSIS_JSON,
        "w",
        encoding="utf-8",
    ) as file:

        json.dump(
            crop_statistics,
            file,
            indent=4,
        )

    # --------------------------------------------------------
    # Print report
    # --------------------------------------------------------

    print("=" * 70)
    print("PlantScan AI - Dataset Analysis")
    print("=" * 70)

    print(
        f"\nImages analyzed : "
        f"{len(rows):,}"
    )

    print(
        f"Minimum class threshold : "
        f"{MIN_CLASS_IMAGES}"
    )

    print("\n" + "-" * 70)

    for crop in sorted(
        crop_statistics
    ):

        stats = crop_statistics[crop]

        print(
            f"\n{crop.upper()}"
        )

        print(
            f"  Total images       : "
            f"{stats['total_images']:,}"
        )

        print(
            f"  Original classes   : "
            f"{stats['number_of_original_classes']}"
        )

        print(
            f"  Healthy images     : "
            f"{stats['healthy_images']:,}"
        )

        print(
            f"  Disease images     : "
            f"{stats['disease_images']:,}"
        )

        print(
            f"  Smallest class     : "
            f"{stats['minimum_class_images']:,}"
        )

        print(
            f"  Largest class      : "
            f"{stats['maximum_class_images']:,}"
        )

        print(
            f"  Classes >= 100     : "
            f"{stats['classes_with_at_least_100_images']}"
        )

        print("  Classes:")

        for class_key, count in sorted(
            stats["classes"].items()
        ):

            source, class_name = class_key.split(
                "::",
                maxsplit=1,
            )

            marker = (
                "OK"
                if count >= MIN_CLASS_IMAGES
                else "LOW"
            )

            print(
                f"    [{marker:<3}] "
                f"{source:<15} "
                f"{class_name:<50} "
                f"{count:,}"
            )

    print("\n" + "=" * 70)

    print("Reports:")
    print(
        f"  CSV  : {ANALYSIS_CSV}"
    )
    print(
        f"  JSON : {ANALYSIS_JSON}"
    )

    print("\nAnalysis completed.")
    print("=" * 70)


# ============================================================
# Main
# ============================================================

if __name__ == "__main__":
    analyze_dataset()