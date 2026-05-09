from pydantic import BaseModel


class SentinelAnalysisRequest(BaseModel):
    lat: float
    lon: float
    start_date: str  # Dinh dang 'YYYY-MM-DD'
    end_date: str    # Dinh dang 'YYYY-MM-DD'
    cloud_cover: float = 5.0  # Muc do may toi da (%)


class SentinelAnalysisResponse(BaseModel):
    lat: float
    lon: float
    start_date: str
    end_date: str
    cloud_cover: float
    sentinel_image_url: str
    # segmentation_base64: str