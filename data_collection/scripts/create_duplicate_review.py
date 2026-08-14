from pathlib import Path
import csv
from PIL import Image


PROJECT_ROOT = Path(__file__).resolve().parents[2]

INPUT_FILE = (
    PROJECT_ROOT
    / "datasets"
    / "reports"
    / "exact_duplicate_groups.csv"
)

OUTPUT_FILE = (
    PROJECT_ROOT
    / "datasets"
    / "reports"
    / "duplicate_review.csv"
)


def get_image_info(relative_path):
    path = PROJECT_ROOT / relative_path.replace("/", "\\")

    try:
        size_bytes = path.stat().st_size

        with Image.open(path) as image:
            width, height = image.size
            image_format = image.format

        return (
            width,
            height,
            image_format,
            size_bytes,
        )

    except Exception as error:
        return (
            "",
            "",
            "",
            f"ERROR: {error}",
        )


def main():

    if not INPUT_FILE.exists():
        print(f"ERROR: {INPUT_FILE} not found.")
        return

    rows = []

    with open(
        INPUT_FILE,
        "r",
        encoding="utf-8",
    ) as file:

        reader = csv.DictReader(file)

        for row in reader:

            leakage = row["split_leakage"] == "YES"
            conflict = row["label_conflict"] == "YES"

            if not leakage and not conflict:
                continue

            files = row["files"].split(" || ")

            for file_path in files:

                width, height, fmt, size = get_image_info(
                    file_path
                )

                rows.append(
                    {
                        "group_id": row["group_id"],
                        "group_size": row["group_size"],
                        "redundant_files": row["redundant_files"],
                        "dataset": row["datasets"],
                        "subsets": row["subsets"],
                        "splits": row["splits"],
                        "labels": row["labels"],
                        "split_leakage": row["split_leakage"],
                        "label_conflict": row["label_conflict"],
                        "sha256": "",
                        "file": file_path,
                        "width": width,
                        "height": height,
                        "format": fmt,
                        "size_bytes": size,
                    }
                )

    fieldnames = [
        "group_id",
        "group_size",
        "redundant_files",
        "dataset",
        "subsets",
        "splits",
        "labels",
        "split_leakage",
        "label_conflict",
        "sha256",
        "file",
        "width",
        "height",
        "format",
        "size_bytes",
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
        writer.writerows(rows)

    print("=" * 70)
    print("PlantScan AI - Duplicate Review Report")
    print("=" * 70)

    print(f"\nSuspicious file entries : {len(rows)}")
    print(f"Report                  : {OUTPUT_FILE}")

    print("\nReview report created.")


if __name__ == "__main__":
    main()