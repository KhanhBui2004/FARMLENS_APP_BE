import os
import ee 
from datetime import datetime

from PIL import Image
from fastapi import APIRouter
from fastapi.responses import JSONResponse
from app.models.sentinelAnalysis import SentinelAnalysisRequest, SentinelAnalysisResponse
from app.schema import sentinel_serial
from app.config.database import analysis_collection
# from app.utils.imageSegmentation import _segment_image_from_url


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

@router.post("/fetch-sentinel-image/")
def get_sentinel_image(payload: SentinelAnalysisRequest):
    try:
        payload_dict = payload.dict()
        
        # 1. Xác định khu vực (Point)
        point = ee.Geometry.Point([payload_dict["lon"], payload_dict["lat"]])

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
        thumb_url = image.getThumbURL({
            'dimensions': 1024,
            'region': point.buffer(10000).bounds(), # 10km quanh điểm
            'format': 'png',
            **vis_params
        })
        
        # segmentation_base64 = _segment_image_from_url(thumb_url)

        response = SentinelAnalysisResponse(
            lat=payload_dict["lat"],
            lon=payload_dict["lon"],
            start_date=payload_dict["start_date"],
            end_date=payload_dict["end_date"],
            cloud_cover=payload_dict["cloud_cover"],
            sentinel_image_url=thumb_url,
            # segmentation_base64=segmentation_base64
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