import calendar
from datetime import datetime, timezone

import ee
import numpy as np
from bson import ObjectId
from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse

from app.models.change_detection_model import ChangeDetectionRequest
from app.schema.change_detection_schema import change_detection_serial
from app.utils.gee import get_region_area_m2
from app.utils.load_model import _segment_image_from_url
from app.utils.segmentation import decode_segmentation_url
from app.utils.jwt import get_current_user

from app.config.database import timeseries_collection


router = APIRouter(prefix="/analysis", tags=["Analysis"])

CLASS_LABELS = [
	"agriculture",
	"barren",
	"forest",
	"rangeland",
	"unknown",
	"urban",
	"water",
]

CLASS_COLORS = [
    [255, 255, 100],  # Agriculture
    [210, 180, 140],  # Barren
    [0, 100, 0],      # Forest
    [124, 252, 0],    # Rangeland
    [0, 0, 0],        # Unknown
    [178, 34, 34],    # Urban
    [65, 105, 225],   # Water
]

def _get_month_range(date_str: str) -> tuple[str, str]:
    parsed = datetime.strptime(date_str, "%Y-%m-%d").date()
    end_date = parsed
    start_month_index = (end_date.month - 1) - 6
    start_year = end_date.year + (start_month_index // 12)
    start_month = (start_month_index % 12) + 1
    last_day = calendar.monthrange(start_year, start_month)[1]
    start_day = min(end_date.day, last_day)
    start_date = end_date.replace(
        year=start_year,
        month=start_month,
        day=start_day,
    )
    return start_date.isoformat(), end_date.isoformat()


@router.get("/change-detection")
def get_change_detection_history(current_user: dict = Depends(get_current_user),):
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

	timeseries = list(timeseries_collection.find({"user_id": user_id}))
	return {
		"code": 200,
		"message": "Change detection history retrieved successfully",
		"data": [change_detection_serial(item) for item in timeseries],
	}


@router.post("/change-detection")
def change_detection(
	payload: ChangeDetectionRequest,
	current_user: dict = Depends(get_current_user),
):
	try:
		if not payload.date1 or not payload.date2:
			return JSONResponse(
				status_code=400,
				content={
					"code": 400,
					"message": "date1 and date2 are required",
				},
			)

		try:
			point = ee.Geometry.Point([payload.lng, payload.lat])
		except Exception:
			return JSONResponse(
				status_code=400,
				content={
					"code": 400,
					"message": "Invalid coordinates",
				},
			)
		date_list = [payload.date1, payload.date2]
		date1 = datetime.strptime(payload.date1, "%Y-%m-%d")
		date2 = datetime.strptime(payload.date2, "%Y-%m-%d")

		if date1 > date2:
			date_list = [payload.date2, payload.date1]
		
		timeline = []
		for date_str in date_list:
			try:
				start_date, end_date = _get_month_range(date_str)
			except ValueError:
				return JSONResponse(
					status_code=400,
					content={
						"code": 400,
						"message": f"Invalid date format: {date_str}",
					},
				)

			collection = (ee.ImageCollection("COPERNICUS/S2_SR_HARMONIZED")
						  .filterBounds(point)
						  .filterDate(start_date, end_date)
						  .filter(ee.Filter.lt("CLOUDY_PIXEL_PERCENTAGE", payload.cloud_cover))
						  .sort("CLOUDY_PIXEL_PERCENTAGE"))

			image = collection.median()

			print("lat:", payload.lat)
			print("lng:", payload.lng)
			print("date_str:", date_str)
			print("start_date:", start_date)
			print("end_date:", end_date)
			print("cloud_cover:", payload.cloud_cover)
			print("image_count:", collection.size().getInfo())
			
			vis_params = {
				"bands": ["B4", "B3", "B2"],
				"min": 0,
				"max": 3000,
				"gamma": 1.4,
			}

			region = point.buffer(2000).bounds()
			thumb_url = image.getThumbURL({
				"dimensions": 1024,
				"region": region,
				"format": "png",
				**vis_params,
			})

			region_area_m2 = get_region_area_m2(region)
			segmentation_url = _segment_image_from_url(thumb_url)
			print('Segmentation URL:', segmentation_url)
			image_array = decode_segmentation_url(segmentation_url)
			print('Decoded image shape:', image_array.shape)

			height, width, _ = image_array.shape
			total_pixels = height * width

			if total_pixels == 0:
				return JSONResponse(
        			status_code=500,
        			content={
            		"code": 500,
            		"message": "Segmentation image has no pixels",
        			},
    			)

			pixel_area_m2 = region_area_m2 / total_pixels
			pixel_area_km2 = float(pixel_area_m2) / 1_000_000.0

			class_stats = {}
			for label, color in zip(CLASS_LABELS, CLASS_COLORS):
				color_array = np.array(color, dtype=np.uint8)
				mask = np.all(image_array == color_array, axis=-1)
				count = int(mask.sum())
				area_km2 = count * pixel_area_km2

				percentage = (count / total_pixels * 100.0) if total_pixels else 0.0

				class_stats[label] = {
					"pixel_count": count,
					"area_km2": round(area_km2, 6),
					"percentage": round(percentage, 4),
				}

			timeline.append({
				"date": end_date,
    			"image_size": {
        			"width": width,
        			"height": height,
    			},
    			"total_pixels": total_pixels,
    			"region_area_m2": region_area_m2,
    			"pixel_area_m2": pixel_area_m2,
    			"classes": class_stats,
			})

		timeseries_doc = {
			"lat": payload.lat,
			"lng": payload.lng,
			"dates": date_list,
			"cloud_cover": payload.cloud_cover,
			"user_id": ObjectId(current_user["sub"]),
			"created_at": datetime.now(timezone.utc),
			"timeline": timeline,
		}
		result = timeseries_collection.insert_one(timeseries_doc)
		timeseries_doc["_id"] = result.inserted_id

		return {
			"code": 200,
			"message": "Change detection results retrieved successfully",
			"data": change_detection_serial(timeseries_doc),
		}
	except Exception as e:
		return JSONResponse(
			status_code=500,
			content={
				"code": 500,
				"message": str(e),
			},
		)


@router.delete("/change-detection")
def delete_change_detection_by_user(
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

	result = timeseries_collection.delete_many({"user_id": user_id})
	if result.deleted_count == 0:
		return JSONResponse(
			status_code=404,
			content={
				"code": 404,
				"message": "No change detection records found",
			},
		)

	return {
		"code": 200,
		"message": "All change detection records deleted successfully",
		"deleted": result.deleted_count,
	}


@router.delete("/change-detection/{change_detection_id}")
def delete_change_detection_by_id(
	change_detection_id: str,
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

	try:
		change_detection_object_id = ObjectId(change_detection_id)
	except Exception:
		return JSONResponse(
			status_code=400,
			content={
				"code": 400,
				"message": "Invalid change_detection_id",
			},
		)

	result = timeseries_collection.delete_one(
		{"_id": change_detection_object_id, "user_id": user_id}
	)
	if result.deleted_count == 0:
		return JSONResponse(
			status_code=404,
			content={
				"code": 404,
				"message": "Change detection not found",
			},
		)

	return {
		"code": 200,
		"message": "Change detection deleted successfully",
	}

