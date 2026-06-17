# from typing import Any


# def _safe_area_km2(class_data: dict | None) -> float:
#     if not class_data:
#         return 0.0
#     return float(class_data.get("area_km2", 0.0))


# def _safe_percentage(class_data: dict | None) -> float:
#     if not class_data:
#         return 0.0
#     return float(class_data.get("percentage", 0.0))


# def build_farmland_tracking(
#     first_timeline: dict[str, Any],
#     second_timeline: dict[str, Any],
# ) -> dict[str, float]:
#     first_agri = first_timeline.get("classes", {}).get("agriculture", {})
#     second_agri = second_timeline.get("classes", {}).get("agriculture", {})

#     previous_area_km2 = _safe_area_km2(first_agri)
#     current_area_km2 = _safe_area_km2(second_agri)

#     previous_percentage = _safe_percentage(first_agri)
#     current_percentage = _safe_percentage(second_agri)

#     change_km2 = current_area_km2 - previous_area_km2
#     change_percentage_points = current_percentage - previous_percentage

#     relative_change_percentage = 0.0
#     if previous_area_km2 > 0:
#         relative_change_percentage = (change_km2 / previous_area_km2) * 100.0

#     return {
#         "previous_agriculture_area_km2": round(previous_area_km2, 6),
#         "current_agriculture_area_km2": round(current_area_km2, 6),
#         "previous_agriculture_percentage": round(previous_percentage, 4),
#         "current_agriculture_percentage": round(current_percentage, 4),
#         "agriculture_change_km2": round(change_km2, 6),
#         "agriculture_change_percentage_points": round(change_percentage_points, 4),
#         "agriculture_relative_change_percentage": round(relative_change_percentage, 4),
#     }


# def detect_abnormality(
#     farmland_tracking: dict[str, float],
# ) -> dict[str, Any]:
#     relative_change = farmland_tracking["agriculture_relative_change_percentage"]
#     point_change = farmland_tracking["agriculture_change_percentage_points"]

#     status = "stable"
#     label = "Ổn định"
#     priority_check = False
#     reason = "Khu vực tương đối ổn định."

#     # Giảm mạnh -> cần kiểm tra thực địa
#     if relative_change <= -10 or point_change <= -8:
#         status = "field_check"
#         label = "Cần kiểm tra thực địa"
#         priority_check = True
#         reason = "Diện tích đất nông nghiệp giảm mạnh, cần kiểm tra thực địa."

#     # Giảm nhẹ hoặc tăng đáng kể -> theo dõi thêm
#     elif relative_change <= -3 or point_change <= -3:
#         status = "monitor"
#         label = "Cần theo dõi thêm"
#         priority_check = False
#         reason = "Diện tích đất nông nghiệp có xu hướng giảm, nên theo dõi thêm."

#     elif relative_change >= 10 or point_change >= 8:
#         status = "monitor"
#         label = "Biến động đáng chú ý"
#         priority_check = False
#         reason = "Diện tích đất nông nghiệp tăng đáng kể, nên theo dõi thêm để xác nhận xu hướng."

#     elif relative_change >= 3 or point_change >= 3:
#         status = "monitor"
#         label = "Theo dõi định kỳ"
#         priority_check = False
#         reason = "Diện tích đất nông nghiệp có biến động, nên tiếp tục theo dõi."

#     return {
#         "status": status,
#         "label": label,
#         "priority_check": priority_check,
#         "reason": reason,
#     }


# def generate_recommendation(
#     farmland_tracking: dict[str, float],
#     abnormality: dict[str, Any],
# ) -> dict[str, Any]:
#     current_percentage = farmland_tracking["current_agriculture_percentage"]
#     relative_change = farmland_tracking["agriculture_relative_change_percentage"]
#     status = abnormality["status"]

#     actions: list[str] = []

#     if status == "field_check":
#         summary = "Đất canh tác giảm đáng kể. Nên kiểm tra thực địa để xác định nguyên nhân biến động."
#         actions.append("Ưu tiên kiểm tra thực địa khu vực này.")
#         actions.append("Đối chiếu thêm với tình hình sử dụng đất thực tế.")
#         actions.append("Phân tích lại ở kỳ tiếp theo để xác nhận xu hướng.")

#     elif status == "monitor":
#         if relative_change > 0:
#             summary = "Diện tích đất canh tác tăng đáng kể. Nên theo dõi thêm để xác nhận đây là xu hướng ổn định."
#             actions.append("Tiếp tục theo dõi trong các kỳ tiếp theo.")
#             actions.append("Đánh giá xem biến động có lặp lại theo thời gian hay không.")
#         else:
#             summary = "Đất canh tác có biến động giảm. Nên tăng tần suất theo dõi trong các kỳ tiếp theo."
#             actions.append("Theo dõi thêm trong các kỳ tiếp theo.")
#             actions.append("Chuẩn bị kiểm tra thực địa nếu xu hướng giảm tiếp tục.")

#     else:
#         summary = "Khu vực tương đối ổn định, có thể tiếp tục sản xuất và theo dõi định kỳ."
#         actions.append("Duy trì theo dõi định kỳ.")

#     if current_percentage >= 50:
#         actions.insert(0, "Khu vực hiện vẫn có đặc trưng đất canh tác rõ rệt.")
#     elif current_percentage >= 25:
#         actions.insert(0, "Đất canh tác vẫn hiện diện nhưng không chiếm ưu thế.")
#     else:
#         actions.insert(0, "Tỷ lệ đất canh tác hiện đang ở mức thấp trong khu vực phân tích.")

#     return {
#         "status": status,
#         "summary": summary,
#         "actions": actions,
#     }

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
    relative_change = farmland_tracking["agriculture_relative_change_percentage"]
    point_change = farmland_tracking["agriculture_change_percentage_points"]

    status = "stable"
    label = "Ổn định"
    priority_check = False
    reason = "Khu vực tương đối ổn định."

    if relative_change <= -10 or point_change <= -8:
        status = "field_check"
        label = "Cần kiểm tra thực địa"
        priority_check = True
        reason = "Diện tích đất nông nghiệp giảm mạnh, cần kiểm tra thực địa."

    elif relative_change <= -3 or point_change <= -3:
        status = "monitor"
        label = "Cần theo dõi thêm"
        priority_check = False
        reason = "Diện tích đất nông nghiệp có xu hướng giảm, nên theo dõi thêm."

    elif relative_change >= 10 or point_change >= 8:
        status = "monitor"
        label = "Biến động đáng chú ý"
        priority_check = False
        reason = "Diện tích đất nông nghiệp tăng đáng kể, nên theo dõi thêm để xác nhận xu hướng."

    elif relative_change >= 3 or point_change >= 3:
        status = "monitor"
        label = "Theo dõi định kỳ"
        priority_check = False
        reason = "Diện tích đất nông nghiệp có biến động, nên tiếp tục theo dõi."

    return {
        "status": status,
        "label": label,
        "priority_check": priority_check,
        "reason": reason,
    }


def _class_percentage_change(
    first_timeline: dict[str, Any],
    second_timeline: dict[str, Any],
    class_name: str,
) -> float:
    first_classes = first_timeline.get("classes", {})
    second_classes = second_timeline.get("classes", {})

    first_pct = float(first_classes.get(class_name, {}).get("percentage", 0.0))
    second_pct = float(second_classes.get(class_name, {}).get("percentage", 0.0))
    return round(second_pct - first_pct, 4)


def generate_secondary_insights(
    first_timeline: dict[str, Any],
    second_timeline: dict[str, Any],
) -> list[str]:
    insights: list[str] = []

    urban_change = _class_percentage_change(first_timeline, second_timeline, "urban")
    water_change = _class_percentage_change(first_timeline, second_timeline, "water")
    barren_change = _class_percentage_change(first_timeline, second_timeline, "barren")
    forest_change = _class_percentage_change(first_timeline, second_timeline, "forest")
    rangeland_change = _class_percentage_change(first_timeline, second_timeline, "rangeland")

    if urban_change >= 5:
        insights.append(
            "Diện tích đất đô thị tăng đáng kể, cần theo dõi khả năng thu hẹp đất canh tác."
        )
    elif urban_change <= -5:
        insights.append(
            "Diện tích đất đô thị giảm đáng kể so với kỳ trước."
        )

    if water_change >= 5:
        insights.append(
            "Diện tích mặt nước tăng đáng kể, cần kiểm tra ảnh hưởng đến khu vực sản xuất nông nghiệp."
        )
    elif water_change <= -5:
        insights.append(
            "Diện tích mặt nước giảm đáng kể so với kỳ trước."
        )

    if barren_change >= 5:
        insights.append(
            "Diện tích đất trống tăng, cần kiểm tra khả năng đất bỏ hoang hoặc thay đổi trạng thái canh tác."
        )
    elif barren_change <= -5:
        insights.append(
            "Diện tích đất trống giảm đáng kể so với kỳ trước."
        )

    if forest_change >= 5:
        insights.append(
            "Diện tích rừng tăng đáng kể, cho thấy độ phủ thực vật của khu vực cao hơn."
        )
    elif forest_change <= -5:
        insights.append(
            "Diện tích rừng giảm đáng kể so với kỳ trước."
        )

    if rangeland_change >= 5:
        insights.append(
            "Diện tích đồng cỏ tăng đáng kể, cần theo dõi thêm để tránh nhầm lẫn với khu vực canh tác."
        )
    elif rangeland_change <= -5:
        insights.append(
            "Diện tích đồng cỏ giảm đáng kể so với kỳ trước."
        )

    return insights


def generate_recommendation(
    farmland_tracking: dict[str, float],
    abnormality: dict[str, Any],
    first_timeline: dict[str, Any],
    second_timeline: dict[str, Any],
) -> dict[str, Any]:
    current_percentage = farmland_tracking["current_agriculture_percentage"]
    relative_change = farmland_tracking["agriculture_relative_change_percentage"]
    status = abnormality["status"]

    actions: list[str] = []

    if status == "field_check":
        summary = "Đất canh tác giảm đáng kể. Nên kiểm tra thực địa để xác định nguyên nhân biến động."
        actions.append("Ưu tiên kiểm tra thực địa khu vực này.")
        actions.append("Đối chiếu thêm với tình hình sử dụng đất thực tế.")
        actions.append("Phân tích lại ở kỳ tiếp theo để xác nhận xu hướng.")

    elif status == "monitor":
        if relative_change > 0:
            summary = "Diện tích đất canh tác tăng đáng kể. Nên theo dõi thêm để xác nhận đây là xu hướng ổn định."
            actions.append("Tiếp tục theo dõi trong các kỳ tiếp theo.")
            actions.append("Đánh giá xem biến động có lặp lại theo thời gian hay không.")
        else:
            summary = "Đất canh tác có biến động giảm. Nên tăng tần suất theo dõi trong các kỳ tiếp theo."
            actions.append("Theo dõi thêm trong các kỳ tiếp theo.")
            actions.append("Chuẩn bị kiểm tra thực địa nếu xu hướng giảm tiếp tục.")

    else:
        summary = "Khu vực tương đối ổn định, có thể tiếp tục sản xuất và theo dõi định kỳ."
        actions.append("Duy trì theo dõi định kỳ.")

    if current_percentage >= 50:
        actions.insert(0, "Khu vực hiện vẫn có đặc trưng đất canh tác rõ rệt.")
    elif current_percentage >= 25:
        actions.insert(0, "Đất canh tác vẫn hiện diện nhưng không chiếm ưu thế.")
    else:
        actions.insert(0, "Tỷ lệ đất canh tác hiện đang ở mức thấp trong khu vực phân tích.")

    secondary_insights = generate_secondary_insights(first_timeline, second_timeline)

    return {
        "status": status,
        "summary": summary,
        "actions": actions,
        "secondary_insights": secondary_insights,
    }