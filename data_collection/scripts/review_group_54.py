from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

PROJECT_ROOT = Path(__file__).resolve().parents[2]

IMAGE_A = (
    PROJECT_ROOT
    / "datasets/raw/Banana/OriginalSet/healthy/122.jpeg"
)

IMAGE_B = (
    PROJECT_ROOT
    / "datasets/raw/Banana/OriginalSet/pestalotiopsis/78.jpeg"
)

OUTPUT = (
    PROJECT_ROOT
    / "datasets/reports/group_54_review.jpg"
)


def load_image(path):
    image = Image.open(path).convert("RGB")
    image.thumbnail((700, 700))
    return image


def main():

    image_a = load_image(IMAGE_A)
    image_b = load_image(IMAGE_B)

    width = 1500
    height = 850

    sheet = Image.new(
        "RGB",
        (width, height),
        "white",
    )

    draw = ImageDraw.Draw(sheet)

    sheet.paste(
        image_a,
        (
            50,
            80,
        ),
    )

    sheet.paste(
        image_b,
        (
            750,
            80,
        ),
    )

    draw.text(
        (50, 30),
        "healthy/122.jpeg",
        fill="black",
    )

    draw.text(
        (750, 30),
        "pestalotiopsis/78.jpeg",
        fill="black",
    )

    sheet.save(
        OUTPUT,
        quality=95,
    )

    print(f"Created: {OUTPUT}")


if __name__ == "__main__":
    main()