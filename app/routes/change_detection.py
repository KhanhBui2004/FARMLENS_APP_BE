import calendar
from datetime import datetime

import ee
import numpy as np
from fastapi import APIRouter
from fastapi.responses import JSONResponse

from app.models.change_detection_model import TimeSeriesRequest
from app.schema.change_detection_schema import timeseries_serial
from app.utils.gee import get_pixel_area_m2
from app.utils.load_model import _segment_image_from_url
from app.utils.segmentation import decode_segmentation_url

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
	[255, 255, 0],
	[232, 184, 153],
	[0, 255, 0],
	[255, 0, 255],
	[0, 0, 0],
	[0, 255, 255],
	[0, 0, 255],
]

def mask_s2_clouds(image):
    qa = image.select('QA60')
    # Bit 10 là mây dày (Opaque clouds), Bit 11 là mây mù (Cirrus clouds)
    cloud_bit_mask = 1 << 10
    
    # Chỉ mask mây dày, tạm thời bỏ qua mây mù để tránh bị trống ảnh
    mask = qa.bitwiseAnd(cloud_bit_mask).eq(0)
    
    return image.updateMask(mask)


def _get_month_range(date_str: str) -> tuple[str, str]:
	parsed = datetime.strptime(date_str, "%Y-%m-%d").date()
	start_date = parsed.replace(day=1)
	end_month_index = (start_date.month - 1) + 3
	end_year = start_date.year + (end_month_index // 12)
	end_month = (end_month_index % 12) + 1
	last_day = calendar.monthrange(end_year, end_month)[1]
	end_date = start_date.replace(year=end_year, month=end_month, day=last_day)
	return start_date.isoformat(), end_date.isoformat()


@router.post("/time-series")
def time_series(payload: TimeSeriesRequest):
	try:
		if not payload.dates:
			return JSONResponse(
				status_code=400,
				content={
					"code": 400,
					"message": "dates is required",
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

		timeline = []
		for date_str in payload.dates:
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
						  .map(mask_s2_clouds)
						  .sort("CLOUDY_PIXEL_PERCENTAGE"))

			image = collection.median().unmask(collection.first())
			
			vis_params = {
				"bands": ["B4", "B3", "B2"],
				"min": 0,
				"max": 3000,
				"gamma": 1.4,
			}

			region = point.buffer(10000).bounds()
			thumb_url = image.getThumbURL({
				"dimensions": 1024,
				"region": region,
				"format": "png",
				**vis_params,
			})

			pixel_area_m2 = get_pixel_area_m2(image, region)
			segmentation_url = _segment_image_from_url(thumb_url)
			image_array = decode_segmentation_url(segmentation_url)

			height, width, _ = image_array.shape
			pixel_area_km2 = float(pixel_area_m2) / 1_000_000.0

			class_stats = {}
			for label, color in zip(CLASS_LABELS, CLASS_COLORS):
				color_array = np.array(color, dtype=np.uint8)
				mask = np.all(image_array == color_array, axis=-1)
				count = int(mask.sum())
				area_km2 = count * pixel_area_km2
				class_stats[label] = {
					"area_km2": round(area_km2, 6),
				}

			timeline.append({
				"date": start_date,
				"classes": class_stats,
			})

		timeseries_doc = {
			"lat": payload.lat,
			"lng": payload.lng,
			"dates": payload.dates,
			"cloud_cover": payload.cloud_cover,
			"created_at": datetime.utcnow(),
			"timeline": timeline,
		}
		result = timeseries_collection.insert_one(timeseries_doc)
		timeseries_doc["_id"] = result.inserted_id

		return {
			"code": 200,
			"message": "Time series retrieved successfully",
			"data": timeseries_serial(timeseries_doc),
		}
	except Exception as e:
		return JSONResponse(
			status_code=500,
			content={
				"code": 500,
				"message": str(e),
			},
		)
