import ee


def get_region_area_m2(region: ee.Geometry) -> float:
    """
    Tính tổng diện tích thực tế của vùng (m²)
    """
    return float(
        region.area(maxError=1).getInfo()
    )


def get_pixel_area_m2(
    region: ee.Geometry,
    image_width: int,
    image_height: int,
) -> float:
    """
    Tính diện tích tương ứng của 1 pixel trên ảnh thumbnail
    """
    total_pixels = image_width * image_height
    region_area_m2 = get_region_area_m2(region)

    return region_area_m2 / total_pixels