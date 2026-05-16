import io
import os
from urllib.parse import urlparse
from urllib.request import urlopen
import uuid

import numpy as np
from PIL import Image

SENTINELS_DIR = os.path.join("storage", "sentinels")
SENTINELS_URL_PREFIX = "/storage/sentinels"

def _local_path_from_storage_url(segmentation_url: str) -> str:
    normalized = segmentation_url.lstrip("/")
    return os.path.abspath(os.path.join(os.getcwd(), normalized))


def decode_segmentation_url(segmentation_url: str) -> np.ndarray:
    parsed = urlparse(segmentation_url)
    if parsed.scheme in {"http", "https"}:
        if parsed.path.startswith("/storage/"):
            local_path = _local_path_from_storage_url(parsed.path)
            image = Image.open(local_path).convert("RGB")
            return np.asarray(image, dtype=np.uint8)
        with urlopen(segmentation_url) as response:
            image_bytes = response.read()
        image = Image.open(io.BytesIO(image_bytes)).convert("RGB")
        return np.asarray(image, dtype=np.uint8)

    if segmentation_url.startswith("/storage/") or segmentation_url.startswith("storage/"):
        local_path = _local_path_from_storage_url(segmentation_url)
        image = Image.open(local_path).convert("RGB")
        return np.asarray(image, dtype=np.uint8)

    image = Image.open(segmentation_url).convert("RGB")
    return np.asarray(image, dtype=np.uint8)

def _download_sentinel_image(image_url: str) -> str:
    os.makedirs(SENTINELS_DIR, exist_ok=True)
    file_name = f"sentinel_{uuid.uuid4().hex}.png"
    file_path = os.path.join(SENTINELS_DIR, file_name)
    with urlopen(image_url) as response:
        image_bytes = response.read()
    with open(file_path, "wb") as file_handle:
        file_handle.write(image_bytes)
    return f"{SENTINELS_URL_PREFIX}/{file_name}"
