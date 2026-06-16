from typing import Any


def _safe_area_km2(class_data: dict | None) -> float:
    if not class_data:
        return 0.0
    return float(class_data.get("area_km2", 0.0))


def _safe_percentage(class_data: dict | None) -> float:
    if not class_data:
        return 0.0
    return float(class_data.get("percentage", 0.0))


def build_farmland_tracking(
    first_timeline: dict[str, Any],
    second_timeline: dict[str, Any],
) -> dict[str, float]:
    first_agri = first_timeline.get("classes", {}).get("agriculture", {})
    second_agri = second_timeline.get("classes", {}).get("agriculture", {})

    previous_area_km2 = _safe_area_km2(first_agri)
    current_area_km2 = _safe_area_km2(second_agri)

    previous_percentage = _safe_percentage(first_agri)
    current_percentage = _safe_percentage(second_agri)

    change_km2 = current_area_km2 - previous_area_km2
    change_percentage_points = current_percentage - previous_percentage

    relative_change_percentage = 0.0
    if previous_area_km2 > 0:
        relative_change_percentage = (change_km2 / previous_area_km2) * 100.0

    return {
        "previous_agriculture_area_km2": round(previous_area_km2, 6),
        "current_agriculture_area_km2": round(current_area_km2, 6),
        "previous_agriculture_percentage": round(previous_percentage, 4),
        "current_agriculture_percentage": round(current_percentage, 4),
        "agriculture_change_km2": round(change_km2, 6),
        "agriculture_change_percentage_points": round(change_percentage_points, 4),
        "agriculture_relative_change_percentage": round(relative_change_percentage, 4),
    }


def detect_abnormality(
    farmland_tracking: dict[str, float],
) -> dict[str, Any]:
    agri_relative_change = farmland_tracking["agriculture_relative_change_percentage"]
    agri_points_change = farmland_tracking["agriculture_change_percentage_points"]

    level = "low"
    priority_check = False
    reason = "Khu vực tương đối ổn định."

    if agri_relative_change <= -10 or agri_points_change <= -8:
        level = "high"
        priority_check = True
        reason = "Diện tích đất nông nghiệp giảm đáng kể."
    elif agri_relative_change <= -5 or agri_points_change <= -4:
        level = "medium"
        priority_check = True
        reason = "Diện tích đất nông nghiệp có xu hướng giảm."
    elif agri_relative_change >= 8:
        level = "medium"
        priority_check = False
        reason = "Diện tích đất nông nghiệp tăng đáng kể."
    else:
        level = "low"
        priority_check = False
        reason = "Biến động đất nông nghiệp chưa đáng kể."

    return {
        "level": level,
        "priority_check": priority_check,
        "reason": reason,
    }


def generate_recommendation(
    farmland_tracking: dict[str, float],
    abnormality: dict[str, Any],
) -> dict[str, Any]:
    current_percentage = farmland_tracking["current_agriculture_percentage"]
    relative_change = farmland_tracking["agriculture_relative_change_percentage"]

    actions: list[str] = []
    summary = "Khu vực ổn định, có thể tiếp tục theo dõi định kỳ."
    status = "stable"

    if current_percentage >= 50:
        actions.append("Khu vực hiện vẫn có đặc trưng đất canh tác rõ rệt.")
    elif current_percentage >= 25:
        actions.append("Đất canh tác vẫn hiện diện nhưng không chiếm ưu thế.")
    else:
        actions.append("Tỷ lệ đất canh tác đang ở mức thấp trong khu vực phân tích.")

    if abnormality["priority_check"]:
        status = "need_field_check"
        summary = "Có dấu hiệu biến động đáng chú ý. Nên kiểm tra thực địa."
        actions.append("Ưu tiên kiểm tra thực địa khu vực này.")
        actions.append("Thực hiện phân tích lại ở kỳ tiếp theo để xác nhận xu hướng.")
    elif relative_change <= -3:
        status = "monitor_closely"
        summary = "Đất canh tác có xu hướng giảm. Nên theo dõi thêm."
        actions.append("Tăng tần suất theo dõi trong các kỳ tiếp theo.")
    else:
        status = "stable"
        summary = "Khu vực tương đối ổn định, có thể tiếp tục sản xuất và theo dõi định kỳ."
        actions.append("Duy trì theo dõi định kỳ.")

    return {
        "status": status,
        "summary": summary,
        "actions": actions,
    }