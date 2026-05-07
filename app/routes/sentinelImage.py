import ee 
import os
from fastapi import APIRouter
from fastapi.responses import JSONResponse

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

router = APIRouter(prefix="/sentinel", tags=["Sentinel-2"])

@router.get("/get-sentinel-image/")
def get_sentinel_image(
    lat: float = 16.0544,       # Ví dụ Đà Nẵng
    lon: float = 108.2022,
    start_date: str = "2024-01-01",
    end_date: str = "2024-12-31",
    cloud_cover: float = 5.0
):
    try:
        # 1. Xác định khu vực (Point)
        point = ee.Geometry.Point([lon, lat])

        # 2. Lọc bộ dữ liệu Sentinel-2
        collection = (ee.ImageCollection('COPERNICUS/S2_SR_HARMONIZED')
                      .filterBounds(point)
                      .filterDate(start_date, end_date)
                      .filter(ee.Filter.lt('CLOUDY_PIXEL_PERCENTAGE', cloud_cover))
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

        # Trả về URL ảnh
        return {
            "code": 200,
            "message": "Sentinel image retrieved successfully",
            "data": {
                "url": thumb_url
            }
        }

    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={
                "code": 500,
                "message": str(e)
            }
        )