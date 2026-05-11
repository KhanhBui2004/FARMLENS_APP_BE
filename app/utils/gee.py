import ee


def get_pixel_area_m2(image: ee.Image, region: ee.Geometry, scale: int = 10) -> float:
    pixel_area = ee.Image.pixelArea()
    stats = pixel_area.reduceRegion(
        reducer=ee.Reducer.mean(),
        geometry=region,
        scale=scale,
        maxPixels=1e9,
        bestEffort=True,
    )
    return float(stats.get("area").getInfo())
