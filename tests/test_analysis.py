from bson import ObjectId


def test_post_segmentation(client):
    payload = {"lat": 0.0, "lng": 0.0, "date": "2023-01-01", "cloud_cover": 10}
    res = client.post("/analysis/segmentation", json=payload)
    body = res.json()
    assert body["code"] == 200, f"segmentation failed: {body}"
    data = body["data"]
    assert "segmentation_url" in data


def test_get_segmentation_history(client):
    res = client.get("/analysis/segmentation")
    body = res.json()
    assert body["code"] == 200
    assert isinstance(body["data"], list)


def test_delete_segmentation_by_id(client):
    analysis_id = str(client.analysis_id)
    res = client.delete(f"/analysis/segmentation/{analysis_id}")
    body = res.json()
    assert body["code"] == 200


def test_delete_all_segmentations(client):
    # Delete all segmentations for user
    res2 = client.delete("/analysis/segmentation")
    body2 = res2.json()
    assert body2["code"] == 200
    assert "deleted" in body2


def test_post_statistics(client):
    analysis_id = str(client.analysis_id)
    res = client.post("/analysis/statistics", json={"analysis_id": analysis_id})
    body = res.json()
    assert body["code"] == 200
    assert "data" in body
    data = body["data"]
    assert "classes" in data
    # Expected class keys exist
    expected = [
        "agriculture",
        "barren",
        "forest",
        "rangeland",
        "unknown",
        "urban",
        "water",
    ]
    for k in expected:
        assert k in data["classes"]


def test_get_statistics_by_analysis_id(client):
    analysis_id = str(client.analysis_id)
    res = client.get(f"/analysis/statistics?analysis_id={analysis_id}")
    body = res.json()
    assert body["code"] == 200
    assert "data" in body


def test_delete_statistics_by_analysis_id(client):
    analysis_id = str(client.analysis_id)
    res2 = client.delete(f"/analysis/statistics/{analysis_id}")
    body2 = res2.json()
    assert body2["code"] == 200


def test_delete_all_statistics(client):
    res3 = client.delete("/analysis/statistics")
    body3 = res3.json()
    assert body3["code"] in (200, 404)
