from pathlib import Path
import csv
import hashlib


# ============================================================
# PlantScan AI - Verify Near Duplicates
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parents[2]

INPUT_FILE = (
    PROJECT_ROOT
    / "datasets"
    / "reports"
    / "near_duplicate_images.csv"
)

OUTPUT_FILE = (
    PROJECT_ROOT
    / "datasets"
    / "reports"
    / "near_duplicate_verified.csv"
)


# ============================================================
# SHA-256
# ============================================================

def calculate_sha256(path):

    sha256 = hashlib.sha256()

    with open(path, "rb") as file:

        while True:

            chunk = file.read(1024 * 1024)

            if not chunk:
                break

            sha256.update(chunk)

    return sha256.hexdigest()


# ============================================================
# Identify dataset
# ============================================================

def get_dataset(path):

    parts = [part.lower() for part in path.parts]

    if "banana"in parts:
        return "Banana"

    if "cotton" in parts:
        return "Cotton"

    if "mango" in parts:
        return "Mango"

    if "rice" in parts:
        return "Rice"

    if "plantdoc" in parts:
        return "PlantDoc"

    if "plantvillage" in parts:
        return "PlantVillage"

    return "Unknown"


# ============================================================
# Identify subset
# ============================================================

def get_subset(path):

    parts = [part.lower() for part in path.parts]

    if "augmentedset" in parts:
        return "Augmented"

    if "originalset" in parts:
        return "Original"

    return "Main"


# ============================================================
# Identify crop
# ============================================================

def get_crop(path):

    parts = list(path.parts)

    try:

        raw_index = next(
            i
            for i, part in enumerate(parts)
            if part.lower() == "raw"
        )

        if raw_index + 1 < len(parts):

            dataset = parts[
                raw_index + 1
            ]

            dataset_lower = dataset.lower()

            if dataset_lower in {
                "bananA".lower(),
                "cotton",
                "mango",
                "rice",
                "plantdoc",
                "plantvillage",
            }:

                # For PlantDoc / PlantVillage,
                # crop is usually determined from
                # the class directory.

                if dataset_lower in {
                    "plantdoc",
                    "plantvillage",
                }:

                    if raw_index + 2 < len(parts):
                        return parts[
                            raw_index + 2
                        ]

                return dataset

    except StopIteration:
        pass

    return "Unknown"


# ============================================================
# Main
# ============================================================

def main():

    print("=" * 70)
    print("PlantScan AI - Verify Near Duplicates")
    print("=" * 70)

    if not INPUT_FILE.exists():

        print(
            f"\nERROR: Input report not found:\n"
            f"{INPUT_FILE}"
        )

        return

    # --------------------------------------------------------
    # Read candidate pairs
    # --------------------------------------------------------

    pairs = []

    with open(
        INPUT_FILE,
        "r",
        encoding="utf-8",
    ) as file:

        reader = csv.DictReader(file)

        for row in reader:

            # We concentrate on the strongest
            # candidates first.
            if int(row["distance"]) == 0:

                pairs.append(row)

    print(
        f"\nDistance-0 pairs : "
        f"{len(pairs):,}"
    )

    # --------------------------------------------------------
    # Cache hashes
    # --------------------------------------------------------

    hash_cache = {}

    results = []

    # --------------------------------------------------------
    # Verify each pair
    # --------------------------------------------------------

    for index, row in enumerate(
        pairs,
        start=1,
    ):

        image_a = (
            PROJECT_ROOT
            / row["image_a"]
        )

        image_b = (
            PROJECT_ROOT
            / row["image_b"]
        )

        if str(image_a) not in hash_cache:

            hash_cache[str(image_a)] = (
                calculate_sha256(image_a)
            )

        if str(image_b) not in hash_cache:

            hash_cache[str(image_b)] = (
                calculate_sha256(image_b)
            )

        hash_a = hash_cache[
            str(image_a)
        ]

        hash_b = hash_cache[
            str(image_b)
        ]

        exact_duplicate = (
            hash_a == hash_b
        )

        dataset_a = get_dataset(
            Path(row["image_a"])
        )

        dataset_b = get_dataset(
            Path(row["image_b"])
        )

        subset_a = get_subset(
            Path(row["image_a"])
        )

        subset_b = get_subset(
            Path(row["image_b"])
        )

        crop_a = get_crop(
            Path(row["image_a"])
        )

        crop_b = get_crop(
            Path(row["image_b"])
        )

        results.append(
            {
                "distance": row["distance"],
                "image_a": row["image_a"],
                "image_b": row["image_b"],
                "sha256_a": hash_a,
                "sha256_b": hash_b,
                "exact_duplicate": (
                    "YES"
                    if exact_duplicate
                    else "NO"
                ),
                "dataset_a": dataset_a,
                "dataset_b": dataset_b,
                "subset_a": subset_a,
                "subset_b": subset_b,
                "crop_a": crop_a,
                "crop_b": crop_b,
            }
        )

        if index % 100 == 0:

            print(
                f"Verified "
                f"{index:,}/"
                f"{len(pairs):,}"
            )

    # --------------------------------------------------------
    # Save report
    # --------------------------------------------------------

    OUTPUT_FILE.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    fieldnames = [
        "distance",
        "image_a",
        "image_b",
        "sha256_a",
        "sha256_b",
        "exact_duplicate",
        "dataset_a",
        "dataset_b",
        "subset_a",
        "subset_b",
        "crop_a",
        "crop_b",
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

        writer.writerows(results)

    # --------------------------------------------------------
    # Summary
    # --------------------------------------------------------

    exact_count = sum(
        1
        for row in results
        if row["exact_duplicate"] == "YES"
    )

    perceptual_only = (
        len(results) - exact_count
    )

    print("\n" + "=" * 70)
    print("VERIFICATION SUMMARY")
    print("=" * 70)

    print(
        f"\nDistance-0 pairs     : "
        f"{len(results):,}"
    )

    print(
        f"Exact duplicates     : "
        f"{exact_count:,}"
    )

    print(
        f"Perceptual only      : "
        f"{perceptual_only:,}"
    )

    # --------------------------------------------------------
    # Dataset relationships
    # --------------------------------------------------------

    relationships = {}

    for row in results:

        relationship = (
            f"{row['dataset_a']} "
            f"<-> "
            f"{row['dataset_b']}"
        )

        relationships[relationship] = (
            relationships.get(
                relationship,
                0,
            )
            + 1
        )

    print(
        "\n--- Dataset Relationships ---"
    )

    for relationship, count in sorted(
        relationships.items(),
        key=lambda item: item[1],
        reverse=True,
    ):

        print(
            f"{relationship:35s}"
            f"{count:,}"
        )

    # --------------------------------------------------------
    # Exact duplicate relationships
    # --------------------------------------------------------

    exact_relationships = {}

    for row in results:

        if row["exact_duplicate"] != "YES":
            continue

        relationship = (
            f"{row['dataset_a']} "
            f"<-> "
            f"{row['dataset_b']}"
        )

        exact_relationships[
            relationship
        ] = (
            exact_relationships.get(
                relationship,
                0,
            )
            + 1
        )

    print(
        "\n--- Exact Duplicate Relationships ---"
    )

    for relationship, count in sorted(
        exact_relationships.items(),
        key=lambda item: item[1],
        reverse=True,
    ):

        print(
            f"{relationship:35s}"
            f"{count:,}"
        )

    print(
        "\n--- Report ---"
    )

    print(
        OUTPUT_FILE
    )

    print(
        "\nVerification completed."
    )

    print("=" * 70)


if __name__ == "__main__":
    main()