import os
from urllib.parse import urlparse
from urllib.request import urlopen

import cv2
import numpy as np
from bson import ObjectId
from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse

from app.config.database import analysis_collection, overlays_collection
from app.models.visualization_model import OverlayRequest
from app.utils.segmentation import decode_segmentation_url
from app.utils.jwt import get_current_user


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


@router.get("/overlay")
def get_overlays(analysis_id: str = None):

	overlays = overlays_collection.find({"analysis_id": analysis_id}).first()
	data = {
			"analysis_id": overlays.get("analysis_id"),
			"overlay_url": overlays.get("overlay_url"),
			}

	return {
		"code": 200,
		"message": "Overlays retrieved successfully",
		"data": data,
	}


@router.post("/overlay")
def create_overlay(
	payload: OverlayRequest,
	current_user: dict = Depends(get_current_user),
):
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
			"user_id": ObjectId(current_user["sub"]),
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


@router.delete("/overlay")
def delete_overlays_by_user(
	current_user: dict = Depends(get_current_user),
):
	try:
		user_id = ObjectId(current_user["sub"])
	except Exception:
		return JSONResponse(
			status_code=401,
			content={
				"code": 401,
				"message": "Invalid token",
			},
		)

	result = overlays_collection.delete_many({"user_id": user_id})
	if result.deleted_count == 0:
		return JSONResponse(
			status_code=404,
			content={
				"code": 404,
				"message": "No overlays found",
			},
		)

	return {
		"code": 200,
		"message": "All overlays deleted successfully",
		"deleted": result.deleted_count,
	}


@router.delete("/overlay/{analysis_id}")
def delete_overlays_by_analysis(
	analysis_id: str,
	current_user: dict = Depends(get_current_user),
):
	try:
		user_id = ObjectId(current_user["sub"])
	except Exception:
		return JSONResponse(
			status_code=401,
			content={
				"code": 401,
				"message": "Invalid token",
			},
		)

	result = overlays_collection.delete_many(
		{"analysis_id": analysis_id, "user_id": user_id}
	)
	if result.deleted_count == 0:
		return JSONResponse(
			status_code=404,
			content={
				"code": 404,
				"message": "Overlay not found",
			},
		)

	return {
		"code": 200,
		"message": "Overlay deleted successfully",
		"deleted": result.deleted_count,
	}
