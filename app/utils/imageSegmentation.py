# import io
# import base64
# import os
# from urllib.request import urlopen
# from PIL import Image
# import numpy as np
# import torch
# import segmentation_models_pytorch as smp



# ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
# MODEL_PATH = os.path.join(ROOT_DIR, "unet_mobilenet_v2_smp_best.pth")
# MODEL_INPUT_SIZE = (512, 512)
# NUM_CLASSES = 7


# def _clean_state_dict(state_dict: dict) -> dict:
#     cleaned = {}
#     for key, value in state_dict.items():
#         if key.startswith("module."):
#             key = key[len("module."):]
#         if key.startswith("model."):
#             key = key[len("model."):]
#         cleaned[key] = value
#     return cleaned


# def _load_model() -> torch.nn.Module:
#     model = smp.Unet(
#         encoder_name="mobilenet_v2",
#         encoder_weights=None,
#         in_channels=3,
#         classes=NUM_CLASSES,
#         activation=None
#     )
#     state = torch.load(MODEL_PATH, map_location="cpu")
#     if isinstance(state, dict) and "state_dict" in state:
#         state = state["state_dict"]
#     model.load_state_dict(_clean_state_dict(state), strict=True)
#     model.eval()
#     return model


# SEGMENTATION_MODEL = _load_model()


# def _segment_image_from_url(image_url: str) -> str:
#     with urlopen(image_url) as response:
#         image_bytes = response.read()

#     image = Image.open(io.BytesIO(image_bytes)).convert("RGB")
#     image = image.resize(MODEL_INPUT_SIZE)

#     image_array = np.asarray(image).astype("float32") / 255.0
#     image_tensor = torch.from_numpy(image_array).permute(2, 0, 1).unsqueeze(0)

#     with torch.no_grad():
#         logits = SEGMENTATION_MODEL(image_tensor)
#         mask = torch.argmax(logits, dim=1).squeeze(0).cpu().numpy().astype("uint8")

#     mask_image = Image.fromarray(mask, mode="L")
#     buffer = io.BytesIO()
#     mask_image.save(buffer, format="PNG")
#     return base64.b64encode(buffer.getvalue()).decode("utf-8")
