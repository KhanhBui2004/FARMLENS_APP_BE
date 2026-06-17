def change_detection_serial(timeseries) -> dict:
    created_at = timeseries.get("created_at")
    if hasattr(created_at, "isoformat"):
        created_at = created_at.isoformat()

    return {
        "id": str(timeseries.get("_id")) if timeseries.get("_id") else None,
        "lat": timeseries.get("lat"),
        "lng": timeseries.get("lng"),
        "dates": timeseries.get("dates"),
        "cloud_cover": timeseries.get("cloud_cover"),
        "created_at": created_at,
        "timeline": timeseries.get("timeline", []),
        "farmland_tracking": timeseries.get("farmland_tracking", {}),
        "abnormality": timeseries.get("abnormality", {}),
        "recommendation": timeseries.get("recommendation", {}),
    }
