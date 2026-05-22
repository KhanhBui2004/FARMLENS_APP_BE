from pydantic import BaseModel


class ChangeDetectionRequest(BaseModel):
    lat: float = 16.0544
    lng: float = 108.2022
    date1: str = "2023-01-01"  # Dinh dang 'YYYY-MM-DD'
    date2: str = "2023-04-01"  # Dinh dang 'YYYY-MM-DD'
    cloud_cover: float = 20.0
