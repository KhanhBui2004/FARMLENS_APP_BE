import io
import os
import uuid
from urllib.request import urlopen
from PIL import Image
import numpy as np
import torch
import segmentation_models_pytorch as smp

# ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
MODEL_PATH = ("unet_resnet50_imagenet_exp_best.pth")
MODEL_INPUT_SIZE = (1024, 1024)
NUM_CLASSES = 7

SEGMENTATIONS_DIR = "storage/segmentations"

CLASS_COLORS = [
    [255, 215, 0],    # Agriculture - vàng lúa
    [181, 101, 29],   # Barren - nâu đất
    [34, 139, 34],    # Forest - xanh rừng
    [154, 205, 50],   # Rangeland - xanh vàng nhạt
    [0, 0, 0],        # Unknown
    [220, 20, 60],    # Urban - đỏ đô thị
    [30, 144, 255],   # Water - xanh nước
]

def _label_to_rgb(mask: np.ndarray) -> np.ndarray:
    height, width = mask.shape
    rgb = np.zeros((height, width, 3), dtype=np.uint8)
    for idx, color in enumerate(CLASS_COLORS):
        rgb[mask == idx] = color
    return rgb


def _clean_state_dict(state_dict: dict) -> dict:
    cleaned = {}
    for key, value in state_dict.items():
        if key.startswith("module."):
            key = key[len("module."):]
        if key.startswith("model."):
            key = key[len("model."):]
        cleaned[key] = value
    return cleaned

def _load_model() -> torch.nn.Module:
    model = smp.Unet(
        encoder_name="resnet50",
        encoder_weights=None,   # không load ImageNet lần nữa
        in_channels=3,
        classes=NUM_CLASSES,
        activation=None,
    )

    checkpoint = torch.load(MODEL_PATH, map_location="cpu")

    if isinstance(checkpoint, dict):
        if "model_state_dict" in checkpoint:
            state_dict = checkpoint["model_state_dict"]
        elif "state_dict" in checkpoint:
            state_dict = checkpoint["state_dict"]
        else:
            state_dict = checkpoint
    else:
        state_dict = checkpoint

    model.load_state_dict(_clean_state_dict(state_dict), strict=True)
    model.eval()

    return model


SEGMENTATION_MODEL = _load_model()


def _segment_image_from_url(image_url: str) -> str:
    with urlopen(image_url) as response:
        image_bytes = response.read()

    image = Image.open(io.BytesIO(image_bytes)).convert("RGB")
    original_size = image.size
    image = image.resize(MODEL_INPUT_SIZE)

    image_array = np.asarray(image).astype("float32") / 255.0
    mean = np.array([0.485, 0.456, 0.406], dtype=np.float32)
    std = np.array([0.229, 0.224, 0.225], dtype=np.float32)
    image_array = (image_array - mean) / std
    image_tensor = torch.from_numpy(image_array).permute(2, 0, 1).unsqueeze(0)

    with torch.no_grad():
        logits = SEGMENTATION_MODEL(image_tensor)
        mask = torch.argmax(logits, dim=1).squeeze(0).cpu().numpy().astype("uint8")

    mask_rgb = _label_to_rgb(mask)
    mask_image = Image.fromarray(mask_rgb, mode="RGB")
    mask_image = mask_image.resize(original_size, resample=Image.NEAREST)
    os.makedirs(SEGMENTATIONS_DIR, exist_ok=True)
    file_name = f"segmentation_{uuid.uuid4().hex}.png"
    file_path = os.path.join(SEGMENTATIONS_DIR, file_name)
    mask_image.save(file_path, format="PNG")
    return f"/{SEGMENTATIONS_DIR}/{file_name}"
