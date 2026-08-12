from pathlib import Path
from collections import Counter
from PIL import Image, UnidentifiedImageError
import csv
import json
import warnings


# ============================================================
# PlantScan AI - Dataset Validator v3
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parents[2]

DATASET_ROOT = PROJECT_ROOT / "datasets" / "raw"
REPORT_DIR = PROJECT_ROOT / "datasets" / "reports"

REPORT_DIR.mkdir(parents=True, exist_ok=True)

INVENTORY_FILE = REPORT_DIR / "dataset_inventory.csv"
SUMMARY_FILE = REPORT_DIR / "dataset_summary.json"


# ============================================================
# Supported image extensions
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
# Dataset sources
# ============================================================

KNOWN_SOURCES = {
    "Banana",
    "Cotton",
    "Mango",
    "PlantDoc",
    "PlantVillage",
    "Rice",
}


# ============================================================
# Crop aliases
# ============================================================

CROP_ALIASES = {
    "tomato": "tomato",
    "potato": "potato",
    "apple": "apple",
    "pepper": "pepper",
    "bell pepper": "bell_pepper",
    "bell_pepper": "bell_pepper",
    "corn": "maize",
    "maize": "maize",
    "grape": "grape",
    "peach": "peach",
    "cherry": "cherry",
    "strawberry": "strawberry",
    "raspberry": "raspberry",
    "blueberry": "blueberry",
    "soybean": "soybean",
    "soyabean": "soybean",
    "squash": "squash",
    "banana": "banana",
    "cotton": "cotton",
    "mango": "mango",
    "rice": "rice",
}


# ============================================================
# Text normalization
# ============================================================

def normalize_text(text):
    return (
        text.lower()
        .replace("_", " ")
        .replace("-", " ")
        .replace("___", " ")
        .strip()
    )


# ============================================================
# Detect source
# ============================================================

def detect_source(relative_path):
    """
    Source is the first directory after datasets/raw.

    Example:

    datasets/raw/PlantVillage/Tomato___Early_blight/image.jpg

    Source:
        PlantVillage
    """

    parts = relative_path.parts

    try:
        raw_index = next(
            i
            for i, part in enumerate(parts)
            if normalize_text(part) == "raw"
        )
    except StopIteration:
        return "unknown"

    after_raw = parts[raw_index + 1:]

    if not after_raw:
        return "unknown"

    source = after_raw[0]

    if source in KNOWN_SOURCES:
        return source

    return "unknown"


# ============================================================
# Extract class
# ============================================================

def get_class_name(image_path):
    """
    Immediate parent directory is the original class.
    """

    return image_path.parent.name


# ============================================================
# Detect crop from PlantVillage / PlantDoc class names
# ============================================================

def detect_crop_from_class(class_name):
    """
    Detect crop from class name.

    Examples:

    Tomato___Early_blight
        -> tomato

    Potato___Late_blight
        -> potato

    Pepper__bell___healthy
        -> bell_pepper

    Blueberry leaf
        -> blueberry

    Soyabean leaf
        -> soybean
    """

    normalized = normalize_text(class_name)

    # Bell pepper must be checked before generic pepper.
    if "bell pepper" in normalized:
        return "bell_pepper"

    # Check longer/more specific names first.
    crop_names = sorted(
        CROP_ALIASES.keys(),
        key=len,
        reverse=True,
    )

    for crop_name in crop_names:

        if crop_name in normalized:

            return CROP_ALIASES[crop_name]

    return "unknown"


# ============================================================
# Detect crop
# ============================================================

def detect_crop(relative_path, source, class_name):
    """
    Determine crop based on dataset structure.

    Crop-specific datasets:

        raw/Banana/...
        raw/Cotton/...
        raw/Mango/...
        raw/Rice/...

    PlantVillage / PlantDoc:

        crop is extracted from class name.
    """

    # --------------------------------------------------------
    # Crop-specific datasets
    # --------------------------------------------------------

    if source in {
        "Banana",
        "Cotton",
        "Mango",
        "Rice",
    }:

        return source.lower()

    # --------------------------------------------------------
    # PlantVillage / PlantDoc
    # --------------------------------------------------------

    if source in {
        "PlantVillage",
        "PlantDoc",
    }:

        return detect_crop_from_class(
            class_name
        )

    return "unknown"


# ============================================================
# Validate image
# ============================================================

def validate_image(path):

    captured_warnings = []

    try:

        # ----------------------------------------------------
        # First verification
        # ----------------------------------------------------

        with warnings.catch_warnings(record=True) as warning_list:

            warnings.simplefilter("always")

            with Image.open(path) as image:
                image.verify()

            for warning in warning_list:

                captured_warnings.append(
                    str(warning.message)
                )

        # ----------------------------------------------------
        # Reopen and actually load image
        # ----------------------------------------------------

        with warnings.catch_warnings(record=True) as warning_list:

            warnings.simplefilter("always")

            with Image.open(path) as image:

                width, height = image.size
                image_format = image.format

                image.load()

            for warning in warning_list:

                captured_warnings.append(
                    str(warning.message)
                )

        warning_text = " | ".join(
            dict.fromkeys(captured_warnings)
        )

        if warning_text:
            status = "warning"
        else:
            status = "valid"

        return (
            width,
            height,
            image_format,
            status,
            warning_text,
        )

    except (
        UnidentifiedImageError,
        OSError,
        ValueError,
    ) as error:

        return (
            None,
            None,
            None,
            "corrupt",
            str(error),
        )


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
# Generate report
# ============================================================

def generate_report():

    image_files = get_image_files()

    print("=" * 70)
    print("PlantScan AI - Dataset Validation v3")
    print("=" * 70)

    print(f"\nDataset root : {DATASET_ROOT}")
    print(f"Images found : {len(image_files):,}")

    if not image_files:

        print("\nNo images found.")
        return

    rows = []

    source_counter = Counter()
    crop_counter = Counter()
    class_counter = Counter()

    status_counter = Counter()
    format_counter = Counter()
    resolution_counter = Counter()

    crop_source_counter = Counter()

    valid_count = 0
    warning_count = 0
    corrupt_count = 0

    # --------------------------------------------------------
    # Process images
    # --------------------------------------------------------

    for index, image_path in enumerate(
        image_files,
        start=1,
    ):

        relative_path = image_path.relative_to(
            PROJECT_ROOT
        )

        class_name = get_class_name(
            image_path
        )

        source = detect_source(
            relative_path
        )

        crop = detect_crop(
            relative_path,
            source,
            class_name,
        )

        (
            width,
            height,
            image_format,
            status,
            warning_message,
        ) = validate_image(
            image_path
        )

        # ----------------------------------------------------
        # Counters
        # ----------------------------------------------------

        status_counter[status] += 1
        source_counter[source] += 1
        crop_counter[crop] += 1

        class_counter[
            f"{crop}::{class_name}"
        ] += 1

        crop_source_counter[
            f"{crop}::{source}"
        ] += 1

        if image_format:
            format_counter[
                image_format
            ] += 1

        if width and height:

            resolution_counter[
                f"{width}x{height}"
            ] += 1

        if status == "valid":
            valid_count += 1

        elif status == "warning":
            warning_count += 1

        elif status == "corrupt":
            corrupt_count += 1

        # ----------------------------------------------------
        # Inventory row
        # ----------------------------------------------------

        rows.append(
            {
                "file": str(relative_path),
                "source": source,
                "crop": crop,
                "class": class_name,
                "width": width,
                "height": height,
                "format": image_format,
                "status": status,
                "warning": warning_message,
            }
        )

        # ----------------------------------------------------
        # Progress
        # ----------------------------------------------------

        if index % 1000 == 0:

            print(
                f"Processed "
                f"{index:,}/"
                f"{len(image_files):,} images..."
            )

    # ========================================================
    # Save inventory CSV
    # ========================================================

    with open(
        INVENTORY_FILE,
        "w",
        newline="",
        encoding="utf-8",
    ) as file:

        fieldnames = [
            "file",
            "source",
            "crop",
            "class",
            "width",
            "height",
            "format",
            "status",
            "warning",
        ]

        writer = csv.DictWriter(
            file,
            fieldnames=fieldnames,
        )

        writer.writeheader()
        writer.writerows(rows)

    # ========================================================
    # Save summary JSON
    # ========================================================

    summary = {
        "total_images": len(image_files),

        "validation": {
            "valid": valid_count,
            "warnings": warning_count,
            "corrupt": corrupt_count,
        },

        "sources": dict(
            sorted(
                source_counter.items()
            )
        ),

        "crops": dict(
            sorted(
                crop_counter.items()
            )
        ),

        "formats": dict(
            sorted(
                format_counter.items()
            )
        ),

        "top_resolutions": dict(
            resolution_counter.most_common(20)
        ),

        "crop_source": dict(
            sorted(
                crop_source_counter.items()
            )
        ),

        "classes": dict(
            sorted(
                class_counter.items()
            )
        ),
    }

    with open(
        SUMMARY_FILE,
        "w",
        encoding="utf-8",
    ) as file:

        json.dump(
            summary,
            file,
            indent=4,
        )

    # ========================================================
    # Console summary
    # ========================================================

    print("\n" + "=" * 70)
    print("VALIDATION SUMMARY")
    print("=" * 70)

    print(
        f"\nTotal images : "
        f"{len(image_files):,}"
    )

    print("\n--- Validation ---")

    print(
        f"Valid       : "
        f"{valid_count:,}"
    )

    print(
        f"Warnings    : "
        f"{warning_count:,}"
    )

    print(
        f"Corrupt     : "
        f"{corrupt_count:,}"
    )

    print("\n--- Sources ---")

    for source, count in sorted(
        source_counter.items()
    ):

        print(
            f"{source:<20} "
            f"{count:,}"
        )

    print("\n--- Crops ---")

    for crop, count in sorted(
        crop_counter.items()
    ):

        print(
            f"{crop:<20} "
            f"{count:,}"
        )

    print("\n--- Image Formats ---")

    for image_format, count in sorted(
        format_counter.items()
    ):

        print(
            f"{image_format:<10} "
            f"{count:,}"
        )

    print("\n--- Crop / Source ---")

    for item, count in sorted(
        crop_source_counter.items()
    ):

        crop, source = item.split(
            "::",
            maxsplit=1,
        )

        print(
            f"{crop:<15} | "
            f"{source:<20} | "
            f"{count:,}"
        )

    print("\n--- Reports ---")

    print(
        f"Inventory : "
        f"{INVENTORY_FILE}"
    )

    print(
        f"Summary   : "
        f"{SUMMARY_FILE}"
    )

    print(
        "\nDataset validation completed."
    )

    print("=" * 70)


# ============================================================
# Main
# ============================================================

if __name__ == "__main__":
    generate_report()