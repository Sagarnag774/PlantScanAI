import csv
import random
import shutil
from collections import defaultdict, Counter
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]

SOURCE_ROOT = PROJECT_ROOT / "datasets" / "processed" / "cleaned_raw"
TAXONOMY = PROJECT_ROOT / "datasets" / "reports" / "model" / "final_class_taxonomy_v2.csv"
OUTPUT_ROOT = PROJECT_ROOT / "datasets" / "model" / "tomato"

IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".bmp", ".webp", ".tif", ".tiff"}
SEED = 42

# Only Tomato classes are used in this first model.
TARGET_CROP = "Tomato"


def load_taxonomy():
    """Return {(dataset, raw_class): canonical_class} for Tomato."""
    mapping = {}

    with TAXONOMY.open("r", encoding="utf-8", newline="") as f:
        for row in csv.DictReader(f):
            if row["crop"].strip() != TARGET_CROP:
                continue

            dataset = row["dataset"].strip()
            raw_class = row["raw_class"].strip()
            canonical = row["canonical_class"].strip()

            if not canonical:
                raise ValueError(
                    f"Empty canonical class for {dataset}/{raw_class}"
                )

            key = (dataset, raw_class)

            if key in mapping and mapping[key] != canonical:
                raise ValueError(
                    f"Conflicting taxonomy mapping for {key}: "
                    f"{mapping[key]} vs {canonical}"
                )

            mapping[key] = canonical

    return mapping


def collect_images(mapping):
    """
    Find all Tomato images in the frozen cleaned dataset.

    The taxonomy contains PlantDoc train/test rows separately, but the
    final taxonomy intentionally maps both to the same canonical class.
    We collect recursively and then perform a controlled model split.
    """
    collected = defaultdict(list)

    for (dataset, raw_class), canonical in sorted(mapping.items()):
        class_root = SOURCE_ROOT / dataset

        if not class_root.exists():
            raise FileNotFoundError(
                f"Dataset source missing: {class_root}"
            )

        matches = []

        # Match the raw class as a directory name anywhere under the
        # dataset source. This handles PlantDoc/train and PlantDoc/test.
        for directory in class_root.rglob("*"):
            if directory.is_dir() and directory.name == raw_class:
                for file in directory.rglob("*"):
                    if file.is_file() and file.suffix.lower() in IMAGE_EXTENSIONS:
                        matches.append(file)

        # Avoid accidentally collecting the same physical file twice.
        matches = sorted(set(matches))

        if not matches:
            raise RuntimeError(
                f"No images found for {dataset}/{raw_class}"
            )

        collected[canonical].extend(matches)

    # Deduplicate paths inside each canonical class.
    for canonical in collected:
        collected[canonical] = sorted(set(collected[canonical]))

    return collected


def split_images(images):
    """
    Stratified per-class 80/10/10 split.

    A fixed seed makes the dataset reproducible.
    """
    rng = random.Random(SEED)

    result = {
        "train": defaultdict(list),
        "validation": defaultdict(list),
        "test": defaultdict(list),
    }

    for canonical, files in sorted(images.items()):
        files = list(files)
        rng.shuffle(files)

        n = len(files)

        if n < 10:
            raise ValueError(
                f"Class '{canonical}' has only {n} images; "
                "too small for the 80/10/10 model split."
            )

        n_test = max(1, round(n * 0.10))
        n_val = max(1, round(n * 0.10))

        # Guarantee at least one training image.
        n_train = n - n_val - n_test

        if n_train < 1:
            raise ValueError(
                f"Invalid split for '{canonical}': {n_train}/{n_val}/{n_test}"
            )

        result["train"][canonical] = files[:n_train]
        result["validation"][canonical] = files[n_train:n_train + n_val]
        result["test"][canonical] = files[n_train + n_val:]

    return result


def clean_output():
    if OUTPUT_ROOT.exists():
        raise FileExistsError(
            f"Output already exists: {OUTPUT_ROOT}\n"
            "Delete it manually only if you intentionally want to rebuild it."
        )

    for split in ("train", "validation", "test"):
        (OUTPUT_ROOT / split).mkdir(parents=True, exist_ok=True)


def copy_dataset(splits):
    manifest_path = OUTPUT_ROOT / "manifest.csv"

    manifest_rows = []

    for split in ("train", "validation", "test"):
        for canonical, files in sorted(splits[split].items()):
            destination_dir = OUTPUT_ROOT / split / canonical
            destination_dir.mkdir(parents=True, exist_ok=True)

            for index, source in enumerate(files):
                # Prefix with an index to avoid filename collisions between
                # PlantDoc and PlantVillage.
                destination = destination_dir / (
                    f"{index:06d}_{source.name}"
                )

                shutil.copy2(source, destination)

                manifest_rows.append({
                    "split": split,
                    "canonical_class": canonical,
                    "source_file": str(source.relative_to(PROJECT_ROOT)),
                    "output_file": str(destination.relative_to(PROJECT_ROOT)),
                })

    with manifest_path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "split",
                "canonical_class",
                "source_file",
                "output_file",
            ],
        )
        writer.writeheader()
        writer.writerows(manifest_rows)

    return manifest_rows


def main():
    print("=" * 80)
    print("PlantScan AI - Build Tomato Model Dataset")
    print("=" * 80)

    if not SOURCE_ROOT.exists():
        raise FileNotFoundError(SOURCE_ROOT)

    if not TAXONOMY.exists():
        raise FileNotFoundError(TAXONOMY)

    mapping = load_taxonomy()

    print(f"Taxonomy mappings : {len(mapping)}")

    images = collect_images(mapping)

    print("\n--- Source image counts by canonical class ---")
    for canonical, files in sorted(images.items()):
        print(f"{canonical:40} {len(files):6}")

    total = sum(len(files) for files in images.values())
    print(f"\nTotal Tomato images : {total}")

    splits = split_images(images)

    print("\n--- Model split counts ---")
    totals = Counter()

    for split in ("train", "validation", "test"):
        count = sum(len(files) for files in splits[split].values())
        totals[split] = count
        print(f"{split:12} : {count}")

    print(f"{'TOTAL':12} : {sum(totals.values())}")

    clean_output()

    manifest = copy_dataset(splits)

    print("\n--- Final class counts ---")
    for canonical in sorted(images):
        print(
            f"{canonical:40} "
            f"train={len(splits['train'][canonical]):5} "
            f"val={len(splits['validation'][canonical]):5} "
            f"test={len(splits['test'][canonical]):5}"
        )

    print("\nOutput:")
    print(OUTPUT_ROOT)

    print("\nManifest:")
    print(OUTPUT_ROOT / "manifest.csv")

    print("\nSTATUS: SUCCESS")
    print("Dataset v1 source was not modified.")
    print("No source images were deleted or moved.")


if __name__ == "__main__":
    main()
