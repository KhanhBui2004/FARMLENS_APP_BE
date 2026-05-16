import os
import ee 
import numpy as np
from datetime import datetime

from fastapi import APIRouter
from fastapi.responses import JSONResponse
from bson import ObjectId
from app.models.sentinelAnalysis import (
    SentinelAnalysisRequest,
    SentinelAnalysisResponse,
    SegmentationStatisticsRequest,
)
from app.schema import sentinel_serial, statistic_serial
from app.config.database import analysis_collection, statistics_collection
from app.utils.loadModel import _segment_image_from_url
from app.utils.segmentation import _download_sentinel_image, decode_segmentation_url
from app.utils.gee import get_pixel_area_m2


# Khởi tạo Earth Engine
json_path = "gee_key.json"

try:
    # Khởi tạo bằng Service Account
    credentials = ee.ServiceAccountCredentials(
        os.getenv("GEE_SERVICE_ACCOUNT"), # Copy email ở ảnh của bạn
        json_path
    )
    ee.Initialize(credentials)
except Exception as e:
    # Nếu chưa xác thực, hãy chạy 'earthengine authenticate' trong terminal
    raise Exception("Chưa xác thực GEE. Hãy chạy 'earthengine authenticate'")

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

@router.post("/segmentation")
def get_sentinel_image(payload: SentinelAnalysisRequest):
    try:
        payload_dict = payload.dict()
        
        # 1. Xác định khu vực (Point)
        point = ee.Geometry.Point([payload_dict["lng"], payload_dict["lat"]])

        # 2. Lọc bộ dữ liệu Sentinel-2
        collection = (ee.ImageCollection('COPERNICUS/S2_SR_HARMONIZED')
                      .filterBounds(point)
                      .filterDate(payload_dict["start_date"], payload_dict["end_date"])
                      .filter(ee.Filter.lt('CLOUDY_PIXEL_PERCENTAGE', payload_dict["cloud_cover"]))
                      .sort('CLOUDY_PIXEL_PERCENTAGE'))

        # 3. Lấy ảnh tốt nhất
        image = collection.median()

        # 4. Tham số hiển thị (Red, Green, Blue)
        vis_params = {
            'bands': ['B4', 'B3', 'B2'],
            'min': 0,
            'max': 3000,
            'gamma': 1.4
        }

        # 5. Tạo URL thumbnail
        # region_image = image.visualize(**vis_params) # Optional: visual
        region = point.buffer(10000).bounds()
        thumb_url = image.getThumbURL({
            'dimensions': 1024,
            'region': region, # 10km quanh điểm
            'format': 'png',
            **vis_params
        })

        pixel_area_m2 = get_pixel_area_m2(image, region)
        
        sentinel_local_url = _download_sentinel_image(thumb_url)
        segmentation_url = _segment_image_from_url(thumb_url)

        response = SentinelAnalysisResponse(
            lat=payload_dict["lat"],
            lng=payload_dict["lng"],
            start_date=payload_dict["start_date"],
            end_date=payload_dict["end_date"],
            cloud_cover=payload_dict["cloud_cover"],
            sentinel_url=sentinel_local_url,
            segmentation_url=segmentation_url,
            pixel_area_m2=pixel_area_m2,
        ).dict()
        response["created_at"] = datetime.utcnow()
        result = analysis_collection.insert_one(response)
        response["_id"] = result.inserted_id

        # Trả về URL ảnh
        return {
            "code": 200,
            "message": "Sentinel image retrieved successfully",
            "data": sentinel_serial(response)
        }

    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={
                "code": 500,
                "message": str(e)
            }
        )
    
@router.post("/statistics")
def get_statistics(payload: SegmentationStatisticsRequest):
    try:
        segmentation_url = payload.segmentation_url
        pixel_area_m2 = payload.pixel_area_m2

        if payload.analysis_id:
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

            segmentation_url = analysis.get("segmentation_url")
            pixel_area_m2 = analysis.get("pixel_area_m2")

        if not segmentation_url:
            return JSONResponse(
                status_code=400,
                content={
                    "code": 400,
                    "message": "segmentation_url is required",
                },
            )

        if not pixel_area_m2:
            return JSONResponse(
                status_code=400,
                content={
                    "code": 400,
                    "message": "pixel_area_m2 is required",
                },
            )

        image_array = decode_segmentation_url(segmentation_url)
        height, width, _ = image_array.shape
        total_pixels = height * width
        pixel_area_km2 = float(pixel_area_m2) / 1_000_000.0

        class_stats = {}
        matched_pixels = 0
        for label, color in zip(CLASS_LABELS, CLASS_COLORS):
            color_array = np.array(color, dtype=np.uint8)
            mask = np.all(image_array == color_array, axis=-1)
            count = int(mask.sum())
            matched_pixels += count
            percentage = (count / total_pixels * 100.0) if total_pixels else 0.0
            area_km2 = count * pixel_area_km2
            class_stats[label] = {
                "pixel_count": count,
                "area_km2": round(area_km2, 6),
                "percentage": round(percentage, 4),
            }

        unmatched = total_pixels - matched_pixels
        statistics_doc = {
            "analysis_id": payload.analysis_id,
            "created_at": datetime.utcnow(),
            "image_size": {"width": width, "height": height},
            "total_pixels": total_pixels,
            "unmatched_pixels": unmatched,
            "pixel_area_m2": pixel_area_m2,
            "classes": class_stats,
        }
        result = statistics_collection.insert_one(statistics_doc)
        statistics_doc["_id"] = result.inserted_id
        return {
            "code": 200,
            "message": "Statistics retrieved successfully",
            "data": statistic_serial(statistics_doc)
        }
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={
                "code": 500,
                "message": str(e)
            }
        )