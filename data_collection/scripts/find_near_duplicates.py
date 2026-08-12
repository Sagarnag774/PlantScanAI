from pathlib import Path
import csv
from collections import defaultdict

from PIL import Image, UnidentifiedImageError
import imagehash


# ============================================================
# PlantScan AI - Near Duplicate Detection
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parents[2]

DATASET_ROOT = PROJECT_ROOT / "datasets" / "raw"
REPORT_DIR = PROJECT_ROOT / "datasets" / "reports"

REPORT_FILE = REPORT_DIR / "near_duplicate_images.csv"


# ============================================================
# Configuration
# ============================================================

IMAGE_EXTENSIONS = {
    ".jpg",
    ".jpeg",
    ".png",
    ".bmp",
    ".webp",
    ".tif",
    ".tiff",
    ".mpo",
}

# Perceptual hash distance.
#
# 0 = perceptually identical
# 1-4 = very similar
# 5-8 = increasingly different
#
# We start conservatively with 4.
HASH_DISTANCE_THRESHOLD = 4


# ============================================================
# Find image files
# ============================================================

def get_image_files():

    if not DATASET_ROOT.exists():
        return []

    return [
        path
        for path in DATASET_ROOT.rglob("*")
        if (
            path.is_file()
            and path.suffix.lower() in IMAGE_EXTENSIONS
        )
    ]


# ============================================================
# Calculate perceptual hash
# ============================================================

def calculate_hash(image_path):

    try:

        with Image.open(image_path) as image:

            # Convert all supported images to RGB
            # before calculating the perceptual hash.
            image = image.convert("RGB")

            return imagehash.phash(image)

    except (
        UnidentifiedImageError,
        OSError,
        ValueError,
    ):

        return None


# ============================================================
# Main
# ============================================================

def find_near_duplicates():

    print("=" * 70)
    print("PlantScan AI - Near Duplicate Detection")
    print("=" * 70)

    image_files = get_image_files()

    print(
        f"\nImages found : {len(image_files):,}"
    )

    print(
        f"Hash threshold : "
        f"{HASH_DISTANCE_THRESHOLD}"
    )

    if not image_files:

        print("\nNo images found.")
        return

    # --------------------------------------------------------
    # Calculate perceptual hashes
    # --------------------------------------------------------

    hashed_images = []
    failed_images = []

    for index, image_path in enumerate(
        image_files,
        start=1,
    ):

        file_hash = calculate_hash(
            image_path
        )

        if file_hash is None:

            failed_images.append(
                image_path
            )

        else:

            hashed_images.append(
                (
                    image_path,
                    file_hash,
                )
            )

        if index % 1000 == 0:

            print(
                f"Processed "
                f"{index:,}/"
                f"{len(image_files):,} images..."
            )

    print(
        f"\nSuccessfully hashed : "
        f"{len(hashed_images):,}"
    )

    print(
        f"Failed to hash       : "
        f"{len(failed_images):,}"
    )

    # --------------------------------------------------------
    # Create coarse hash buckets
    # --------------------------------------------------------

    buckets = defaultdict(list)

    for image_path, file_hash in hashed_images:

        bucket_key = str(file_hash)[:8]

        buckets[bucket_key].append(
            (
                image_path,
                file_hash,
            )
        )

    # --------------------------------------------------------
    # Compare images inside buckets
    # --------------------------------------------------------

    duplicate_groups = []

    for bucket_images in buckets.values():

        if len(bucket_images) < 2:
            continue

        for i in range(
            len(bucket_images)
        ):

            path_a, hash_a = bucket_images[i]

            for j in range(
                i + 1,
                len(bucket_images),
            ):

                path_b, hash_b = bucket_images[j]

                distance = (
                    hash_a - hash_b
                )

                if (
                    distance
                    <= HASH_DISTANCE_THRESHOLD
                ):

                    duplicate_groups.append(
                        {
                            "path_a": path_a,
                            "path_b": path_b,
                            "distance": distance,
                            "hash_a": str(hash_a),
                            "hash_b": str(hash_b),
                        }
                    )

    # --------------------------------------------------------
    # Sort matches by similarity
    # --------------------------------------------------------

    duplicate_groups.sort(
        key=lambda item: item["distance"]
    )

    # --------------------------------------------------------
    # Create report directory
    # --------------------------------------------------------

    REPORT_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    # --------------------------------------------------------
    # Save CSV report
    # --------------------------------------------------------

    with open(
        REPORT_FILE,
        "w",
        newline="",
        encoding="utf-8",
    ) as file:

        writer = csv.writer(file)

        writer.writerow(
            [
                "distance",
                "image_a",
                "image_b",
                "hash_a",
                "hash_b",
            ]
        )

        for group in duplicate_groups:

            image_a = str(
                group["path_a"].relative_to(
                    PROJECT_ROOT
                )
            )

            image_b = str(
                group["path_b"].relative_to(
                    PROJECT_ROOT
                )
            )

            writer.writerow(
                [
                    group["distance"],
                    image_a,
                    image_b,
                    group["hash_a"],
                    group["hash_b"],
                ]
            )

    # --------------------------------------------------------
    # Distance distribution
    # --------------------------------------------------------

    distance_counts = defaultdict(int)

    for group in duplicate_groups:

        distance_counts[
            group["distance"]
        ] += 1

    # --------------------------------------------------------
    # Results
    # --------------------------------------------------------

    print("\n" + "=" * 70)
    print("NEAR DUPLICATE ANALYSIS")
    print("=" * 70)

    print(
        f"\nNear-duplicate pairs : "
        f"{len(duplicate_groups):,}"
    )

    print(
        f"Failed images        : "
        f"{len(failed_images):,}"
    )

    print("\n--- Distance Distribution ---")

    if not distance_counts:

        print(
            "No near-duplicate pairs found."
        )

    else:

        for distance in sorted(
            distance_counts
        ):

            print(
                f"Distance {distance}: "
                f"{distance_counts[distance]:,} pairs"
            )

    # --------------------------------------------------------
    # Show first 20 matches
    # --------------------------------------------------------

    print("\n--- First 20 Matches ---")

    if not duplicate_groups:

        print(
            "No suspicious pairs found."
        )

    else:

        for index, group in enumerate(
            duplicate_groups[:20],
            start=1,
        ):

            print(
                f"\nGroup {index}"
            )

            print(
                f"Distance: "
                f"{group['distance']}"
            )

            print(
                "  A: "
                + str(
                    group["path_a"].relative_to(
                        PROJECT_ROOT
                    )
                )
            )

            print(
                "  B: "
                + str(
                    group["path_b"].relative_to(
                        PROJECT_ROOT
                    )
                )
            )

    # --------------------------------------------------------
    # Failed images
    # --------------------------------------------------------

    if failed_images:

        print(
            "\n--- Failed Images ---"
        )

        for image_path in failed_images[:20]:

            print(
                "  "
                + str(
                    image_path.relative_to(
                        PROJECT_ROOT
                    )
                )
            )

    # --------------------------------------------------------
    # Report location
    # --------------------------------------------------------

    print(
        "\n--- Report ---"
    )

    print(
        REPORT_FILE
    )

    print(
        "\nNear-duplicate detection completed."
    )

    print("=" * 70)


# ============================================================
# Entry point
# ============================================================

if __name__ == "__main__":
    find_near_duplicates()