from typing import Optional
from pydantic import BaseModel


class SentinelAnalysisRequest(BaseModel):
    lat: float = 16.0544
    lng: float = 108.2022
    start_date: str = "2023-01-01"  # Dinh dang 'YYYY-MM-DD'
    end_date: str = "2023-12-31"    # Dinh dang 'YYYY-MM-DD'
    cloud_cover: float = 5.0  # Muc do may toi da (%)


class SentinelAnalysisResponse(BaseModel):
    lat: float
    lng: float
    start_date: str
    end_date: str
    cloud_cover: float
    sentinel_url: str
    segmentation_url: str
    pixel_area_m2: Optional[float] = None


class SegmentationStatisticsRequest(BaseModel):
    analysis_id: Optional[str] = None
    segmentation_url: Optional[str] = None
    pixel_area_m2: Optional[float] = None