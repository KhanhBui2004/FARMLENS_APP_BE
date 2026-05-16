import os
from urllib.parse import urlparse
from urllib.request import urlopen

import cv2
import numpy as np
from bson import ObjectId
from fastapi import APIRouter
from fastapi.responses import JSONResponse

from app.config.database import analysis_collection, overlays_collection
from app.models.visualization_model import OverlayRequest
from app.utils.segmentation import decode_segmentation_url


router = APIRouter(prefix="/visualization", tags=["Visualization"])

OVERLAYS_DIR = os.path.join("storage", "overlays")
OVERLAYS_URL_PREFIX = "/storage/overlays"


def _local_path_from_storage_url(path_value: str) -> str:
	normalized = path_value.lstrip("/")
	return os.path.abspath(os.path.join(os.getcwd(), normalized))


def _decode_image_from_url(image_url: str) -> np.ndarray:
	parsed = urlparse(image_url)
	if parsed.scheme in {"http", "https"}:
		if parsed.path.startswith("/storage/"):
			local_path = _local_path_from_storage_url(parsed.path)
			return cv2.imread(local_path, cv2.IMREAD_COLOR)
		with urlopen(image_url) as response:
			image_bytes = response.read()
		image_array = np.frombuffer(image_bytes, dtype=np.uint8)
		return cv2.imdecode(image_array, cv2.IMREAD_COLOR)

	if image_url.startswith("/storage/") or image_url.startswith("storage/"):
		local_path = _local_path_from_storage_url(image_url)
		return cv2.imread(local_path, cv2.IMREAD_COLOR)

	return cv2.imread(image_url, cv2.IMREAD_COLOR)


@router.post("/overlay")
def create_overlay(payload: OverlayRequest):
	try:
		try:
			analysis = analysis_collection.find_one({"_id": ObjectId(payload.analysis_id)})
		except Exception:
			return JSONResponse(
				status_code=400,
				content={
					"code": 400,
					"message": "Invalid analysis_id",
				},
			)

		if not analysis:
			return JSONResponse(
				status_code=404,
				content={
					"code": 404,
					"message": "Analysis not found",
				},
			)

		sentinel_url = analysis.get("sentinel_url")
		segmentation_url = analysis.get("segmentation_url")

		if not sentinel_url or not segmentation_url:
			return JSONResponse(
				status_code=400,
				content={
					"code": 400,
					"message": "sentinel_url and segmentation_url are required",
				},
			)

		satellite = _decode_image_from_url(sentinel_url)
		segmentation_rgb = decode_segmentation_url(segmentation_url)
		segmentation = cv2.cvtColor(segmentation_rgb, cv2.COLOR_RGB2BGR)

		height, width = satellite.shape[:2]
		segmentation = cv2.resize(segmentation, (width, height), interpolation=cv2.INTER_NEAREST)

		overlay = cv2.addWeighted(
			satellite,
			0.7,
			segmentation,
			0.3,
			0,
		)

		os.makedirs(OVERLAYS_DIR, exist_ok=True)
		file_name = f"overlay_{payload.analysis_id}.png"
		file_path = os.path.join(OVERLAYS_DIR, file_name)
		cv2.imwrite(file_path, overlay)

		# Save overlay information to the database
		overlays_collection.insert_one({
			"analysis_id": payload.analysis_id,
			"overlay_url": f"{OVERLAYS_URL_PREFIX}/{file_name}",
		})

		return {
			"code": 200,
			"message": "Overlay created successfully",
			"data": {
				"analysis_id": payload.analysis_id,
				"overlay_url": f"{OVERLAYS_URL_PREFIX}/{file_name}",
			},
		}
	except Exception as e:
		return JSONResponse(
			status_code=500,
			content={
				"code": 500,
				"message": str(e),
			},
		)
