from pathlib import Path
import csv
from collections import Counter


ROOT = Path("datasets/processed/cleaned_raw")
REPORT_DIR = Path("datasets/reports/model")
REPORT_DIR.mkdir(parents=True, exist_ok=True)

OUTPUT = REPORT_DIR / "class_inventory.csv"

IMAGE_EXTENSIONS = {
    ".jpg", ".jpeg", ".png",
    ".bmp", ".webp", ".tif", ".tiff"
}


def find_images(root):
    return [
        p for p in root.rglob("*")
        if p.is_file()
        and p.suffix.lower() in IMAGE_EXTENSIONS
    ]


def detect_dataset(path):
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


def detect_split(path):
    parts = {p.lower() for p in path.parts}

    if "train" in parts:
        return "train"

    if "test" in parts:
        return "test"

    if "validation" in parts or "val" in parts:
        return "validation"

    return "raw"


def main():

    images = find_images(ROOT)

    print("=" * 70)
    print("PlantScan AI - Model Class Inventory")
    print("=" * 70)

    print(f"\nImages scanned: {len(images):,}")

    counts = Counter()

    for path in images:

        dataset = detect_dataset(path)
        split = detect_split(path)

        label = path.parent.name

        counts[
            (dataset, split, label)
        ] += 1

    with open(
        OUTPUT,
        "w",
        newline="",
        encoding="utf-8"
    ) as f:

        writer = csv.writer(f)

        writer.writerow([
            "dataset",
            "split",
            "class",
            "image_count"
        ])

        for key in sorted(counts):

            writer.writerow([
                key[0],
                key[1],
                key[2],
                counts[key]
            ])

    print(f"\nReport:")
    print(OUTPUT)

    print("\n--- Classes ---")

    class_totals = Counter()

    for (dataset, split, label), count in counts.items():
        class_totals[label] += count

    for label, count in sorted(
        class_totals.items(),
        key=lambda x: (-x[1], x[0])
    ):
        print(
            f"{label:45} {count:6,}"
        )

    print(
        f"\nUnique folder labels: "
        f"{len(class_totals)}"
    )


if __name__ == "__main__":
    main()