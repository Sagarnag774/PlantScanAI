from pathlib import Path
import csv
import re


# ============================================================
# PlantScan AI - Canonical Class Mapping
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parents[2]

REPORT_DIR = PROJECT_ROOT / "datasets" / "reports"

INVENTORY_FILE = REPORT_DIR / "dataset_inventory.csv"
MAPPING_FILE = REPORT_DIR / "class_mapping.csv"


# ============================================================
# Disease rules
# ============================================================

DISEASE_RULES = {

    "early_blight": [
        "early blight",
    ],

    "late_blight": [
        "late blight",
    ],

    "bacterial_spot": [
        "bacterial spot",
    ],

    "bacterial_blight": [
        "bacterial blight",
    ],

    "bacterial_leaf_blight": [
        "bacterial leaf blight",
    ],

    "brown_spot": [
        "brown spot",
    ],

    "leaf_blast": [
        "leaf blast",
    ],

    "leaf_scald": [
        "leaf scald",
    ],

    "sheath_blight": [
        "sheath blight",
    ],

    "anthracnose": [
        "anthracnose",
    ],

    "powdery_mildew": [
        "powdery mildew",
    ],

    "sooty_mould": [
        "sooty mould",
        "sooty mold",
    ],

    "bacterial_canker": [
        "bacterial canker",
    ],

    "curl_virus": [
        "curl virus",
        "yellow leaf curl virus",
        "leaf yellow virus",
    ],

    "mosaic_virus": [
        "mosaic virus",
    ],

    "septoria_leaf_spot": [
        "septoria leaf spot",
    ],

    "target_spot": [
        "target spot",
    ],

    "leaf_mold": [
        "leaf mold",
        "mold leaf",
    ],

    "spider_mites": [
        "spider mites",
        "two spotted spider mite",
    ],

    "fusarium_wilt": [
        "fusarium wilt",
        "fussarium wilt",
    ],

    "sigatoka": [
        "sigatoka",
    ],

    "cordana": [
        "cordana",
    ],

    "pestalotiopsis": [
        "pestalotiopsis",
    ],

    "die_back": [
        "die back",
    ],

    "gall_midge": [
        "gall midge",
    ],

    "cutting_weevil": [
        "cutting weevil",
    ],

    "apple_scab": [
        "apple scab",
    ],

    "rust": [
        "apple rust",
        "corn rust",
    ],

    "leaf_spot": [
        "leaf spot",
    ],

    "black_rot": [
        "black rot",
    ],

    "gray_leaf_spot": [
        "gray leaf spot",
    ],

    "leaf_blight": [
        "leaf blight",
    ],
}


# ============================================================
# Healthy detection
# ============================================================

def is_healthy(class_name):

    normalized = normalize_text(class_name)

    healthy_terms = [
        "healthy",
        "normal",
    ]

    return any(
        term in normalized
        for term in healthy_terms
    )


# ============================================================
# Text normalization
# ============================================================

def normalize_text(text):

    text = text.lower()

    # Handle PlantVillage's triple underscores.
    text = text.replace(
        "___",
        " "
    )

    text = text.replace(
        "__",
        " "
    )

    text = text.replace(
        "_",
        " "
    )

    text = text.replace(
        "-",
        " "
    )

    text = re.sub(
        r"\s+",
        " ",
        text
    )

    return text.strip()


# ============================================================
# Detect disease
# ============================================================

def detect_disease(class_name, crop):

    normalized = normalize_text(
        class_name
    )

    # --------------------------------------------------------
    # Healthy
    # --------------------------------------------------------

    if is_healthy(class_name):

        return (
            "healthy",
            "healthy",
        )

    # --------------------------------------------------------
    # Explicit PlantDoc mappings
    #
    # These are handled before generic rules because some
    # PlantDoc class names are ambiguous.
    # --------------------------------------------------------

    explicit_mappings = {

        "apple scab leaf": (
            "apple_scab",
            "disease",
        ),

        "apple rust leaf": (
            "rust",
            "disease",
        ),

        "bell pepper leaf spot": (
            "leaf_spot",
            "disease",
        ),

        "grape leaf black rot": (
            "black_rot",
            "disease",
        ),

        "corn gray leaf spot": (
            "gray_leaf_spot",
            "disease",
        ),

        "corn leaf blight": (
            "leaf_blight",
            "disease",
        ),

        "corn rust leaf": (
            "rust",
            "disease",
        ),

        "tomato leaf yellow virus": (
            "curl_virus",
            "disease",
        ),
    }

    if normalized in explicit_mappings:

        return explicit_mappings[
            normalized
        ]

    # --------------------------------------------------------
    # Generic disease rules
    # --------------------------------------------------------

    for canonical_name, keywords in DISEASE_RULES.items():

        for keyword in keywords:

            keyword_normalized = normalize_text(
                keyword
            )

            if keyword_normalized in normalized:

                return (
                    canonical_name,
                    "disease",
                )

    # --------------------------------------------------------
    # Unknown
    # --------------------------------------------------------

    return (
        "REVIEW_REQUIRED",
        "unknown",
    )


# ============================================================
# Main mapping generation
# ============================================================

def create_mapping():

    # --------------------------------------------------------
    # Check inventory
    # --------------------------------------------------------

    if not INVENTORY_FILE.exists():

        raise FileNotFoundError(
            "\nInventory file not found:\n"
            f"{INVENTORY_FILE}\n\n"
            "Run this first:\n"
            "python data_collection/scripts/"
            "validate_dataset.py"
        )

    # --------------------------------------------------------
    # Collect unique classes
    # --------------------------------------------------------

    unique_classes = set()

    with open(
        INVENTORY_FILE,
        "r",
        encoding="utf-8",
    ) as file:

        reader = csv.DictReader(file)

        for row in reader:

            key = (
                row["source"],
                row["crop"],
                row["class"],
            )

            unique_classes.add(key)

    # --------------------------------------------------------
    # Generate mapping
    # --------------------------------------------------------

    mappings = []

    for source, crop, original_class in sorted(
        unique_classes
    ):

        canonical_class, class_type = detect_disease(
            original_class,
            crop,
        )

        mappings.append(
            {
                "source": source,
                "crop": crop,
                "original_class": original_class,
                "canonical_class": canonical_class,
                "type": class_type,
            }
        )

    # --------------------------------------------------------
    # Save mapping
    # --------------------------------------------------------

    with open(
        MAPPING_FILE,
        "w",
        newline="",
        encoding="utf-8",
    ) as file:

        fieldnames = [
            "source",
            "crop",
            "original_class",
            "canonical_class",
            "type",
        ]

        writer = csv.DictWriter(
            file,
            fieldnames=fieldnames,
        )

        writer.writeheader()

        writer.writerows(mappings)

    # --------------------------------------------------------
    # Statistics
    # --------------------------------------------------------

    review_count = sum(
        row["canonical_class"]
        == "REVIEW_REQUIRED"
        for row in mappings
    )

    disease_count = sum(
        row["type"]
        == "disease"
        for row in mappings
    )

    healthy_count = sum(
        row["type"]
        == "healthy"
        for row in mappings
    )

    # --------------------------------------------------------
    # Print summary
    # --------------------------------------------------------

    print("=" * 80)
    print("PlantScan AI - Canonical Class Mapping")
    print("=" * 80)

    print(
        f"\nOriginal classes : {len(mappings)}"
    )

    print(
        f"Disease classes  : {disease_count}"
    )

    print(
        f"Healthy classes  : {healthy_count}"
    )

    print(
        f"Review required  : {review_count}"
    )

    print("\n--- Mapping ---")

    for row in mappings:

        print(
            f"{row['source']:<15} | "
            f"{row['crop']:<12} | "
            f"{row['original_class']:<50} | "
            f"{row['canonical_class']:<30} | "
            f"{row['type']}"
        )

    print("\n--- Output ---")

    print(
        f"Mapping file:\n{MAPPING_FILE}"
    )

    print(
        "\nMapping generation completed."
    )

    print("=" * 80)


# ============================================================
# Entry point
# ============================================================

if __name__ == "__main__":
    create_mapping()