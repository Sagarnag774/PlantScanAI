from pathlib import Path
import csv
from PIL import Image, ImageDraw, ImageFont


PROJECT_ROOT = Path(__file__).resolve().parents[2]

INPUT_FILE = (
    PROJECT_ROOT
    / "datasets/reports/exact_duplicate_groups.csv"
)

OUTPUT_FILE = (
    PROJECT_ROOT
    / "datasets/reports/remaining_conflicts_review.jpg"
)

GROUP_IDS = {
    "97",
    "155",
    "191",
    "197",
    "220",
    "226",
}


# ============================================================
# Helpers
# ============================================================

def load_image(path):
    image = Image.open(path).convert("RGB")

    # Keep the full image while fitting it into the panel.
    image.thumbnail((650, 430))

    return image


def get_label_from_path(path):
    """
    The label is the directory immediately before the filename.
    Example:
    .../Potato leaf late blight/image.jpg
    -> Potato leaf late blight
    """

    return Path(path).parent.name


def get_split_from_path(path):
    parts = [part.lower() for part in Path(path).parts]

    if "test" in parts:
        return "TEST"

    if "train" in parts:
        return "TRAIN"

    return "RAW"


def main():

    if not INPUT_FILE.exists():
        print(f"ERROR: Report not found:")
        print(INPUT_FILE)
        return

    groups = []

    with open(
        INPUT_FILE,
        "r",
        encoding="utf-8",
    ) as file:

        reader = csv.DictReader(file)

        for row in reader:

            if row["group_id"] in GROUP_IDS:
                groups.append(row)

    # Sort numerically by group ID.
    groups.sort(
        key=lambda row: int(row["group_id"])
    )

    if not groups:
        print("ERROR: No requested groups found.")
        return

    # --------------------------------------------------------
    # Contact sheet settings
    # --------------------------------------------------------

    panel_width = 700
    panel_height = 540

    total_width = panel_width * 2
    total_height = panel_height * len(groups)

    sheet = Image.new(
        "RGB",
        (
            total_width,
            total_height,
        ),
        "white",
    )

    draw = ImageDraw.Draw(sheet)

    # --------------------------------------------------------
    # Process each duplicate group
    # --------------------------------------------------------

    for row_index, row in enumerate(groups):

        files = row["files"].split(" || ")

        if len(files) != 2:
            print(
                f"WARNING: Group {row['group_id']} "
                f"has {len(files)} files."
            )
            continue

        y_offset = row_index * panel_height

        # Group title
        draw.text(
            (15, y_offset + 10),
            (
                f"GROUP {row['group_id']}  |  "
                f"Labels: {row['labels']}"
            ),
            fill="black",
        )

        for column, file_path in enumerate(files):

            try:

                full_path = (
                    PROJECT_ROOT
                    / file_path
                )

                image = load_image(full_path)

                x_offset = (
                    column * panel_width
                    + 25
                )

                image_y = y_offset + 60

                sheet.paste(
                    image,
                    (
                        x_offset,
                        image_y,
                    ),
                )

                label = get_label_from_path(
                    file_path
                )

                split = get_split_from_path(
                    file_path
                )

                filename = Path(
                    file_path
                ).name

                draw.text(
                    (
                        x_offset,
                        y_offset + 45,
                    ),
                    f"{split} - {label}",
                    fill="black",
                )

                draw.text(
                    (
                        x_offset,
                        image_y + 435,
                    ),
                    filename,
                    fill="black",
                )

            except Exception as error:

                print(
                    f"ERROR loading:"
                    f"\n{file_path}"
                    f"\n{error}"
                )

                draw.text(
                    (
                        column * panel_width + 25,
                        y_offset + 100,
                    ),
                    f"ERROR: {file_path}",
                    fill="red",
                )

    # --------------------------------------------------------
    # Save
    # --------------------------------------------------------

    OUTPUT_FILE.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    sheet.save(
        OUTPUT_FILE,
        quality=95,
    )

    print("=" * 70)
    print("PlantScan AI - Remaining Conflict Review")
    print("=" * 70)

    print(
        f"\nGroups included : "
        f"{len(groups)}"
    )

    print(
        "Groups          : "
        + ", ".join(
            row["group_id"]
            for row in groups
        )
    )

    print(
        f"\nCreated:"
        f"\n{OUTPUT_FILE}"
    )

    print("\nReview image created.")


if __name__ == "__main__":
    main()