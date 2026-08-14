from pathlib import Path
from PIL import Image, ImageDraw

PROJECT_ROOT = Path(__file__).resolve().parents[2]

IMAGE_A = (
    PROJECT_ROOT
    / "datasets/raw/PlantDoc/test/"
    / "Corn leaf blight/"
    / "Corn leaf blight (10).jpg"
)

IMAGE_B = (
    PROJECT_ROOT
    / "datasets/raw/PlantDoc/train/"
    / "Corn Gray leaf spot/"
    / "Corn Gray leaf spot (20).jpg"
)

OUTPUT = (
    PROJECT_ROOT
    / "datasets/reports/group_50_review.jpg"
)


def load_image(path):
    image = Image.open(path).convert("RGB")
    image.thumbnail((700, 700))
    return image


def main():

    image_a = load_image(IMAGE_A)
    image_b = load_image(IMAGE_B)

    sheet = Image.new(
        "RGB",
        (1500, 850),
        "white",
    )

    draw = ImageDraw.Draw(sheet)

    sheet.paste(image_a, (50, 80))
    sheet.paste(image_b, (750, 80))

    draw.text(
    (50, 30),
    "TEST - Corn leaf blight",
    fill="black",
    )

    draw.text(
    (750, 30),
    "TRAIN - Corn Gray leaf spot",
    fill="black",
    )

    sheet.save(
        OUTPUT,
        quality=95,
    )

    print(f"Created: {OUTPUT}")


if __name__ == "__main__":
    main()