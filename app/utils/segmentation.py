import base64
import io

import numpy as np
from PIL import Image


def decode_segmentation_base64(segmentation_base64: str) -> np.ndarray:
    image_bytes = base64.b64decode(segmentation_base64)
    image = Image.open(io.BytesIO(image_bytes)).convert("RGB")
    return np.asarray(image, dtype=np.uint8)
