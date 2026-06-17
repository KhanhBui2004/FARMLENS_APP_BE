from typing import Any


def _pct(class_stats: dict[str, Any], class_name: str) -> float:
    return float(class_stats.get(class_name, {}).get("percentage", 0.0))


def evaluate_current_area(class_stats: dict[str, Any]) -> dict[str, Any]:
    agri = _pct(class_stats, "agriculture")
    urban = _pct(class_stats, "urban")
    barren = _pct(class_stats, "barren")
    water = _pct(class_stats, "water")
    forest = _pct(class_stats, "forest")
    rangeland = _pct(class_stats, "rangeland")

    suitability = "trung bình"
    priority = "theo dõi định kỳ"
    summary = ""
    insights: list[str] = []

    # 1. Đánh giá mức độ phù hợp cho canh tác
    if agri >= 50:
        suitability = "cao"
        summary = "Khu vực hiện có đặc trưng đất canh tác rõ rệt."
        insights.append("Tỷ lệ đất nông nghiệp chiếm ưu thế trong khu vực phân tích.")
    elif agri >= 25:
        suitability = "trung bình"
        summary = "Khu vực có đất canh tác nhưng không chiếm ưu thế."
        insights.append("Đất nông nghiệp hiện diện nhưng bị xen lẫn bởi các lớp phủ khác.")
    else:
        suitability = "thấp"
        summary = "Tỷ lệ đất canh tác thấp trong khu vực phân tích."
        insights.append("Khu vực hiện không thể hiện rõ đặc trưng đất canh tác.")

    # 2. Đánh giá yếu tố đáng chú ý
    if urban >= 20:
        insights.append(
            "Tỷ lệ đất đô thị tương đối cao, cần chú ý khả năng xen lấn đất canh tác."
        )

    if barren >= 20:
        insights.append(
            "Tỷ lệ đất trống cao, cần kiểm tra khả năng đất bỏ hoang hoặc chưa được canh tác."
        )

    if water >= 15:
        insights.append(
            "Tỷ lệ mặt nước đáng kể, cần xem xét ảnh hưởng đến hoạt động sản xuất nông nghiệp."
        )

    if forest >= 20:
        insights.append(
            "Tỷ lệ rừng tương đối cao, cho thấy khu vực có độ phủ thực vật tự nhiên đáng kể."
        )

    if rangeland >= 20:
        insights.append(
            "Tỷ lệ đồng cỏ cao, cần theo dõi thêm để tránh nhầm lẫn với khu vực canh tác."
        )

    # 3. Xếp hạng ưu tiên kiểm tra
    if agri < 25 or urban >= 25 or barren >= 25:
        priority = "ưu tiên kiểm tra"
    elif urban >= 15 or barren >= 15 or water >= 10:
        priority = "cần theo dõi thêm"
    else:
        priority = "theo dõi định kỳ"

    return {
        "suitability": suitability,
        "priority": priority,
        "summary": summary,
        "insights": insights,
        "class_percentages": {
            "agriculture": round(agri, 4),
            "urban": round(urban, 4),
            "barren": round(barren, 4),
            "water": round(water, 4),
            "forest": round(forest, 4),
            "rangeland": round(rangeland, 4),
        },
    }