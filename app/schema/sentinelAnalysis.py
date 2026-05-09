def sentinel_serial(analysis) -> dict:
    return {
        "id": str(analysis.get("_id")) if analysis.get("_id") else None,
        "created_at": analysis.get("created_at"),
        "lat": analysis.get("lat"),
        "lon": analysis.get("lon"),
        "start_date": analysis.get("start_date"),
        "end_date": analysis.get("end_date"),
        "cloud_cover": analysis.get("cloud_cover"),
        "sentinel_image_url": analysis.get("sentinel_image_url"),
        "segmentation_base64": analysis.get("segmentation_base64"),
    }