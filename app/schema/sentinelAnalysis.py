def sentinel_serial(analysis) -> dict:
    return {
        "id": str(analysis.get("_id")) if analysis.get("_id") else None,
        "created_at": analysis.get("created_at"),
        "lat": analysis.get("lat"),
        "lng": analysis.get("lng"),
        "start_date": analysis.get("start_date"),
        "end_date": analysis.get("end_date"),
        "cloud_cover": analysis.get("cloud_cover"),
        "pixel_area_m2": analysis.get("pixel_area_m2"),
        "sentinel_url": analysis.get("sentinel_url"),
        "segmentation_url": analysis.get("segmentation_url"),
    }


def statistic_serial(statistics) -> dict:
    analysis_id = statistics.get("analysis_id")
    if analysis_id is not None:
        analysis_id = str(analysis_id)

    return {
        "id": str(statistics.get("_id")) if statistics.get("_id") else None,
        "analysis_id": analysis_id,
        "created_at": statistics.get("created_at"),
        "image_size": statistics.get("image_size"),
        "total_pixels": statistics.get("total_pixels"),
        "unmatched_pixels": statistics.get("unmatched_pixels"),
        "pixel_area_m2": statistics.get("pixel_area_m2"),
        "classes": statistics.get("classes"),
    }