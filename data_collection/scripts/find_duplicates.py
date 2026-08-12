from pathlib import Path
from collections import defaultdict
import hashlib
import csv


# ============================================================
# PlantScan AI - Exact Duplicate Detection
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parents[2]

DATASET_ROOT = PROJECT_ROOT / "datasets" / "raw"
REPORT_DIR = PROJECT_ROOT / "datasets" / "reports"

DUPLICATE_REPORT = REPORT_DIR / "duplicate_images.csv"


# ============================================================
# Supported image formats
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


# ============================================================
# SHA-256 hash
# ============================================================

def calculate_hash(file_path):

    sha256 = hashlib.sha256()

    with open(
        file_path,
        "rb",
    ) as file:

        while True:

            chunk = file.read(
                1024 * 1024
            )

            if not chunk:
                break

            sha256.update(chunk)

    return sha256.hexdigest()


# ============================================================
# Find images
# ============================================================

def get_image_files():

    if not DATASET_ROOT.exists():
        return []

    return [
        path
        for path in DATASET_ROOT.rglob("*")
        if path.is_file()
        and path.suffix.lower()
        in IMAGE_EXTENSIONS
    ]


# ============================================================
# Main
# ============================================================

def find_duplicates():

    print("=" * 70)
    print("PlantScan AI - Exact Duplicate Detection")
    print("=" * 70)

    image_files = get_image_files()

    print(
        f"\nImages found : "
        f"{len(image_files):,}"
    )

    if not image_files:

        print("\nNo images found.")
        return

    hashes = defaultdict(list)

    # --------------------------------------------------------
    # Calculate hashes
    # --------------------------------------------------------

    for index, image_path in enumerate(
        image_files,
        start=1,
    ):

        try:

            file_hash = calculate_hash(
                image_path
            )

            hashes[file_hash].append(
                image_path
            )

        except (
            OSError,
            IOError,
        ) as error:

            print(
                f"\nCould not read:"
                f"\n{image_path}"
                f"\nError: {error}"
            )

        if index % 1000 == 0:

            print(
                f"Processed "
                f"{index:,}/"
                f"{len(image_files):,} images..."
            )

    # --------------------------------------------------------
    # Extract duplicate groups
    # --------------------------------------------------------

    duplicate_groups = {
        file_hash: paths
        for file_hash, paths in hashes.items()
        if len(paths) > 1
    }

    duplicate_image_count = sum(
        len(paths)
        for paths in duplicate_groups.values()
    )

    extra_duplicate_count = sum(
        len(paths) - 1
        for paths in duplicate_groups.values()
    )

    # --------------------------------------------------------
    # Save report
    # --------------------------------------------------------

    REPORT_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    with open(
        DUPLICATE_REPORT,
        "w",
        newline="",
        encoding="utf-8",
    ) as file:

        writer = csv.writer(file)

        writer.writerow(
            [
                "hash",
                "duplicate_group",
                "file",
            ]
        )

        group_number = 1

        for file_hash, paths in sorted(
            duplicate_groups.items()
        ):

            for image_path in paths:

                relative_path = (
                    image_path
                    .relative_to(PROJECT_ROOT)
                )

                writer.writerow(
                    [
                        file_hash,
                        group_number,
                        str(relative_path),
                    ]
                )

            group_number += 1

    # --------------------------------------------------------
    # Print results
    # --------------------------------------------------------

    print("\n" + "=" * 70)
    print("DUPLICATE ANALYSIS")
    print("=" * 70)

    print(
        f"\nUnique file hashes : "
        f"{len(hashes):,}"
    )

    print(
        f"Duplicate groups   : "
        f"{len(duplicate_groups):,}"
    )

    print(
        f"Images in duplicate groups : "
        f"{duplicate_image_count:,}"
    )

    print(
        f"Extra duplicate images     : "
        f"{extra_duplicate_count:,}"
    )

    print("\n--- Duplicate Groups ---")

    if not duplicate_groups:

        print(
            "\nNo exact duplicates found."
        )

    else:

        for group_number, (
            file_hash,
            paths,
        ) in enumerate(
            sorted(
                duplicate_groups.items()
            ),
            start=1,
        ):

            print(
                f"\nGroup {group_number}"
            )

            print(
                f"SHA-256: "
                f"{file_hash}"
            )

            for image_path in paths:

                print(
                    "  "
                    + str(
                        image_path.relative_to(
                            PROJECT_ROOT
                        )
                    )
                )

    print("\n--- Report ---")

    print(
        DUPLICATE_REPORT
    )

    print(
        "\nExact duplicate detection completed."
    )

    print("=" * 70)


# ============================================================
# Entry point
# ============================================================

if __name__ == "__main__":
    find_duplicates()