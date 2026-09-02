import base64
import io
import pytest
from PIL import Image, ImageDraw
from fastapi.testclient import TestClient
from backend.main import app


@pytest.fixture(scope="session")
def client():
    """Provides a FastAPI TestClient instance."""
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture
def valid_leaf_image_bytes() -> bytes:
    """Generates a synthetic 256x256 image with green textures simulating a leaf."""
    img = Image.new("RGB", (256, 256), color=(34, 139, 34))
    draw = ImageDraw.Draw(img)
    # Draw leaf veins and spots
    draw.line([(128, 20), (128, 236)], fill=(50, 205, 50), width=3)
    draw.line([(128, 80), (60, 120)], fill=(50, 205, 50), width=2)
    draw.line([(128, 120), (190, 160)], fill=(50, 205, 50), width=2)
    draw.ellipse([(90, 90), (110, 110)], fill=(139, 69, 19))  # brown spot
    
    buf = io.BytesIO()
    img.save(buf, format="JPEG")
    return buf.getvalue()


@pytest.fixture
def blank_image_bytes() -> bytes:
    """Generates a plain uniform color image to simulate low-feature uncertain inputs."""
    img = Image.new("RGB", (256, 256), color=(200, 200, 200))
    buf = io.BytesIO()
    img.save(buf, format="JPEG")
    return buf.getvalue()


@pytest.fixture
def tiny_image_bytes() -> bytes:
    """Generates an image that is smaller than minimum required dimensions (10x10)."""
    img = Image.new("RGB", (10, 10), color=(0, 255, 0))
    buf = io.BytesIO()
    img.save(buf, format="JPEG")
    return buf.getvalue()


@pytest.fixture
def corrupt_image_bytes() -> bytes:
    """Generates non-image garbage bytes."""
    return b"NOT_A_VALID_IMAGE_FILE_HEADER_BINARY_DATA_CORRUPT"


@pytest.fixture
def valid_base64_image(valid_leaf_image_bytes) -> str:
    """Returns valid base64-encoded image string."""
    encoded = base64.b64encode(valid_leaf_image_bytes).decode("utf-8")
    return f"data:image/jpeg;base64,{encoded}"
