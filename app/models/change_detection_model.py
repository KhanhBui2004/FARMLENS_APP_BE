from pydantic import BaseModel


class TimeSeriesRequest(BaseModel):
    lat: float = 16.0544
    lng: float = 108.2022
    dates: list[str] = ["2023-01-01", "2023-02-01", "2023-03-01"]  # Dinh dang 'YYYY-MM-DD'
    cloud_cover: float = 20.0
