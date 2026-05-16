def timeseries_serial(timeseries) -> dict:
	return {
		"id": str(timeseries.get("_id")) if timeseries.get("_id") else None,
		"lat": timeseries.get("lat"),
		"lng": timeseries.get("lng"),
		"dates": timeseries.get("dates"),
		"cloud_cover": timeseries.get("cloud_cover"),
		"created_at": timeseries.get("created_at"),
		"timeline": timeseries.get("timeline", []),
	}
