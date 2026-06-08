def test_get_change_detection_history(client):
    res = client.get("/analysis/change-detection")
    body = res.json()
    assert body["code"] == 200
    assert isinstance(body["data"], list)


def test_post_change_detection(client):
    payload = {"lat": 0.0, "lng": 0.0, "date1": "2023-01-01", "date2": "2023-07-01", "cloud_cover": 10}
    res = client.post("/analysis/change-detection", json=payload)
    body = res.json()
    assert body["code"] == 200
    assert "data" in body


def test_delete_all_change_detection(client):
    res2 = client.delete("/analysis/change-detection")
    body2 = res2.json()
    assert body2["code"] in (200, 404)
