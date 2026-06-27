import io
import os
from urllib.parse import urlparse
from urllib.request import urlopen
import uuid
from typing import Any

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

def _pixel_to_lat_lng(
    x: float,
    y: float,
    width: int,
    height: int,
    region_bounds: dict[str, float],
) -> dict[str, float]:
    west = float(region_bounds["west"])
    east = float(region_bounds["east"])
    south = float(region_bounds["south"])
    north = float(region_bounds["north"])

    lng = west + (x / max(width - 1, 1)) * (east - west)
    lat = north - (y / max(height - 1, 1)) * (north - south)

    return {
        "lat": lat,
        "lng": lng,
    }


def _bbox_to_geo(
    bbox: dict[str, int],
    width: int,
    height: int,
    region_bounds: dict[str, float],
) -> dict[str, float]:
    top_left = _pixel_to_lat_lng(
        bbox["x_min"],
        bbox["y_min"],
        width,
        height,
        region_bounds,
    )
    bottom_right = _pixel_to_lat_lng(
        bbox["x_max"],
        bbox["y_max"],
        width,
        height,
        region_bounds,
    )

    return {
        "north": top_left["lat"],
        "south": bottom_right["lat"],
        "west": top_left["lng"],
        "east": bottom_right["lng"],
    }


def _largest_connected_component(mask: np.ndarray) -> dict[str, Any] | None:
    mask_u8 = mask.astype(np.uint8)

    import cv2

    num_labels, labels, stats, centroids = cv2.connectedComponentsWithStats(
        mask_u8,
        connectivity=4,
    )

    # label 0 là background
    if num_labels <= 1:
        return None

    areas = stats[1:, cv2.CC_STAT_AREA]
    best_label = int(np.argmax(areas) + 1)

    x = int(stats[best_label, cv2.CC_STAT_LEFT])
    y = int(stats[best_label, cv2.CC_STAT_TOP])
    w = int(stats[best_label, cv2.CC_STAT_WIDTH])
    h = int(stats[best_label, cv2.CC_STAT_HEIGHT])
    count = int(stats[best_label, cv2.CC_STAT_AREA])

    centroid_x, centroid_y = centroids[best_label]

    # Mask riêng của cụm agriculture lớn nhất
    component_mask = (labels == best_label).astype(np.uint8)

    # Tìm điểm nằm sâu nhất bên trong cụm, phù hợp để đặt marker
    distance = cv2.distanceTransform(component_mask, cv2.DIST_L2, 5)
    _, _, _, max_loc = cv2.minMaxLoc(distance)

    # max_loc trả về dạng (x, y)
    marker_x = float(max_loc[0])
    marker_y = float(max_loc[1])

    return {
        "component_count": int(num_labels - 1),
        "pixel_count": count,
        "bbox": {
            "x_min": x,
            "y_min": y,
            "x_max": x + w - 1,
            "y_max": y + h - 1,
        },
        "centroid": {
            "x": float(centroid_x),
            "y": float(centroid_y),
        },
        "marker_point": {
            "x": marker_x,
            "y": marker_y,
        },
    }


def build_largest_agriculture_survey_region(
    image_array: np.ndarray,
    pixel_area_km2: float,
    region_bounds: dict[str, float] | None = None,
) -> dict[str, Any]:
    agriculture_color = np.array([255, 255, 100], dtype=np.uint8)

    agriculture_mask = np.all(image_array == agriculture_color, axis=-1)
    total_agriculture_pixels = int(agriculture_mask.sum())

    if total_agriculture_pixels == 0:
        return {
            "available": False,
            "label": "agriculture",
            "reason": "Không phát hiện đất nông nghiệp trong khu vực phân tích.",
            "component_count": 0,
            "pixel_count": 0,
            "area_km2": 0.0,
            "percentage_of_agriculture": 0.0,
            "center_lat": None,
            "center_lng": None,
            "bbox": None,
            "bbox_geo": None,
        }

    largest = _largest_connected_component(agriculture_mask)

    if largest is None:
        return {
            "available": False,
            "label": "agriculture",
            "reason": "Không tìm thấy cụm đất nông nghiệp hợp lệ.",
            "component_count": 0,
            "pixel_count": 0,
            "area_km2": 0.0,
            "percentage_of_agriculture": 0.0,
            "center_lat": None,
            "center_lng": None,
            "bbox": None,
            "bbox_geo": None,
        }

    height, width = agriculture_mask.shape

    largest_pixel_count = int(largest["pixel_count"])
    area_km2 = largest_pixel_count * pixel_area_km2
    percentage_of_agriculture = (
        largest_pixel_count / total_agriculture_pixels * 100.0
        if total_agriculture_pixels > 0
        else 0.0
    )

    marker_point = largest.get("marker_point") or largest["centroid"]

    result = {
        "available": True,
        "label": "agriculture",
        "reason": "Đây là cụm đất nông nghiệp liên thông có diện tích lớn nhất trong khu vực phân tích.",
        "component_count": int(largest["component_count"]),
        "pixel_count": largest_pixel_count,
        "area_km2": round(area_km2, 6),
        "percentage_of_agriculture": round(percentage_of_agriculture, 4),

    # Tâm hình học, dùng để tham khảo
        "center_x": round(largest["centroid"]["x"], 2),
        "center_y": round(largest["centroid"]["y"], 2),
        "center_x_ratio": round(largest["centroid"]["x"] / width, 6),
        "center_y_ratio": round(largest["centroid"]["y"] / height, 6),

    # Điểm marker thực tế, nên dùng để vẽ lên ảnh overlay
        "marker_x": round(marker_point["x"], 2),
        "marker_y": round(marker_point["y"], 2),
        "marker_x_ratio": round(marker_point["x"] / width, 6),
        "marker_y_ratio": round(marker_point["y"] / height, 6),

        "bbox": largest["bbox"],
        "centroid": largest["centroid"],
        "center_lat": None,
        "center_lng": None,
        "bbox_geo": None,
    }

    if region_bounds:
        center = _pixel_to_lat_lng(
            largest["centroid"]["x"],
            largest["centroid"]["y"],
            width,
            height,
            region_bounds,
        )

        result["center_lat"] = round(center["lat"], 7)
        result["center_lng"] = round(center["lng"], 7)
        result["bbox_geo"] = _bbox_to_geo(
            largest["bbox"],
            width,
            height,
            region_bounds,
        )

    return result
