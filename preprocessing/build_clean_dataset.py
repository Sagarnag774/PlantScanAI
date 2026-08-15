from pathlib import Path
import csv
import shutil


PROJECT_ROOT = Path(__file__).resolve().parents[1]

RAW_DIR = PROJECT_ROOT / "datasets" / "raw"

OUTPUT_DIR = (
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

LOG_FILE = (
    PROJECT_ROOT
    / "datasets"
    / "reports"
    / "clean_dataset_log.csv"
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


def normalize(path):
    return path.replace("\\", "/")


def load_excluded_files():

    excluded = set()

    with open(
        AUDIT_FILE,
        "r",
        encoding="utf-8",
    ) as file:

        reader = csv.DictReader(file)

        for row in reader:

            decision = row["decision"]

            if decision in {
                "EXCLUDE",
                "EXCLUDE_ALL",
            }:

                excluded.add(
                    normalize(row["file"])
                )

    return excluded


def main():

    print("=" * 70)
    print("PlantScan AI - Build Clean Dataset")
    print("=" * 70)

    # --------------------------------------------------------
    # Safety checks
    # --------------------------------------------------------

    if not RAW_DIR.exists():

        print(
            f"\nERROR: Raw dataset not found:\n"
            f"{RAW_DIR}"
        )

        return

    if not AUDIT_FILE.exists():

        print(
            f"\nERROR: Duplicate audit not found:\n"
            f"{AUDIT_FILE}"
        )

        return

    # --------------------------------------------------------
    # Load exclusion list
    # --------------------------------------------------------

    excluded_files = load_excluded_files()

    print(
        f"\nFiles marked for exclusion : "
        f"{len(excluded_files):,}"
    )

    # --------------------------------------------------------
    # Safety: output must not be inside raw
    # --------------------------------------------------------

    if str(OUTPUT_DIR).lower().startswith(
        str(RAW_DIR).lower()
    ):

        print(
            "\nERROR: Output directory is inside raw dataset."
        )

        return

    # --------------------------------------------------------
    # Create output directory
    # --------------------------------------------------------

    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    # --------------------------------------------------------
    # Counters
    # --------------------------------------------------------

    total_files = 0
    image_files = 0
    copied_files = 0
    excluded_count = 0

    missing_excluded = []

    log_rows = []

    # --------------------------------------------------------
    # Scan raw dataset
    # --------------------------------------------------------

    for source_path in RAW_DIR.rglob("*"):

        if not source_path.is_file():
            continue

        total_files += 1

        relative_path = source_path.relative_to(
            PROJECT_ROOT
        )

        relative_string = normalize(
            str(relative_path)
        )

        is_image = (
            source_path.suffix.lower()
            in IMAGE_EXTENSIONS
        )

        if is_image:
            image_files += 1

        # ----------------------------------------------------
        # Exclusion
        # ----------------------------------------------------

        if relative_string in excluded_files:

            excluded_count += 1

            log_rows.append(
                {
                    "file": relative_string,
                    "action": "EXCLUDED",
                    "reason": "duplicate audit",
                }
            )

            continue

        # ----------------------------------------------------
        # Copy
        # ----------------------------------------------------

        destination = (
            OUTPUT_DIR
            / source_path.relative_to(RAW_DIR)
        )

        destination.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        shutil.copy2(
            source_path,
            destination,
        )

        copied_files += 1

        log_rows.append(
            {
                "file": relative_string,
                "action": "COPIED",
                "reason": "",
            }
        )

    # --------------------------------------------------------
    # Check that every audit exclusion actually existed
    # --------------------------------------------------------

    raw_relative_files = {
        normalize(
            str(path.relative_to(PROJECT_ROOT))
        )
        for path in RAW_DIR.rglob("*")
        if path.is_file()
    }

    for excluded in excluded_files:

        if excluded not in raw_relative_files:

            missing_excluded.append(
                excluded
            )

    # --------------------------------------------------------
    # Write log
    # --------------------------------------------------------

    LOG_FILE.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    with open(
        LOG_FILE,
        "w",
        newline="",
        encoding="utf-8",
    ) as file:

        writer = csv.DictWriter(
            file,
            fieldnames=[
                "file",
                "action",
                "reason",
            ],
        )

        writer.writeheader()
        writer.writerows(log_rows)

    # --------------------------------------------------------
    # Summary
    # --------------------------------------------------------

    print("\n" + "=" * 70)
    print("CLEAN DATASET SUMMARY")
    print("=" * 70)

    print(
        f"\nRaw files scanned       : "
        f"{total_files:,}"
    )

    print(
        f"Image files scanned     : "
        f"{image_files:,}"
    )

    print(
        f"Files copied            : "
        f"{copied_files:,}"
    )

    print(
        f"Files excluded          : "
        f"{excluded_count:,}"
    )

    print(
        f"\nExpected relationship:"
        f"\nCopied + excluded       : "
        f"{copied_files + excluded_count:,}"
    )

    if missing_excluded:

        print(
            "\nWARNING: Excluded files not found:"
        )

        for path in missing_excluded:
            print(f"  {path}")

    else:

        print(
            "\nAll audit exclusions were found "
            "in the raw dataset."
        )

    print(
        f"\nClean dataset:"
        f"\n{OUTPUT_DIR}"
    )

    print(
        f"\nCleaning log:"
        f"\n{LOG_FILE}"
    )

    print(
        "\nIMPORTANT:"
        "\nNo files were deleted from datasets/raw."
    )

    print("=" * 70)


if __name__ == "__main__":
    main()