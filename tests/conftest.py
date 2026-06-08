import os
import sys
import types
from datetime import datetime, timezone
from bson import ObjectId

import pytest
from fastapi.testclient import TestClient
from PIL import Image

# Provide lightweight shims for optional heavy dependencies so tests can run
try:
    import bcrypt  # type: ignore
except ModuleNotFoundError:
    fake_bcrypt = types.ModuleType("bcrypt")
    def gensalt():
        return b"$2b$12$fake_salt___________"
    def hashpw(pw, salt):
        return b"fake" + pw
    def checkpw(pw, hashed):
        return hashed == b"fake" + pw
    fake_bcrypt.gensalt = gensalt
    fake_bcrypt.hashpw = hashpw
    fake_bcrypt.checkpw = checkpw
    sys.modules["bcrypt"] = fake_bcrypt

try:
    import ee  # type: ignore
except ModuleNotFoundError:
    fake_ee = types.ModuleType("ee")
    class ServiceAccountCredentials:
        def __init__(self, *a, **k):
            pass
    def Initialize(credentials=None):
        return None
    class Geometry:
        @staticmethod
        def Point(coords):
            class P:
                def buffer(self, *a, **k):
                    class B:
                        def bounds(self):
                            return None
                    return B()
            return P()
    class Filter:
        @staticmethod
        def lt(field, value):
            return None
    def ImageCollection(name):
        class C:
            def filterBounds(self, *a, **k):
                return self
            def filterDate(self, *a, **k):
                return self
            def filter(self, *a, **k):
                return self
            def sort(self, *a, **k):
                return self
            def median(self):
                return types.SimpleNamespace(getThumbURL=lambda *a, **k: "")
        return C()
    fake_ee.ServiceAccountCredentials = ServiceAccountCredentials
    fake_ee.Initialize = Initialize
    fake_ee.Geometry = Geometry
    fake_ee.Filter = Filter
    fake_ee.ImageCollection = ImageCollection
    sys.modules["ee"] = fake_ee

# Minimal shim for 'jose' package (jwt) to avoid installing python-jose for tests
try:
    from jose import JWTError  # type: ignore
except ModuleNotFoundError:
    import json
    import base64
    class JWTError(Exception):
        pass
    fake_jwt = types.SimpleNamespace()
    def _encode(payload, secret, algorithm=None):
        def default(o):
            if hasattr(o, "isoformat"):
                return o.isoformat()
            return str(o)
        s = json.dumps(payload, default=default)
        return base64.urlsafe_b64encode(s.encode()).decode()
    def _decode(token, secret, algorithms=None):
        try:
            s = base64.urlsafe_b64decode(token.encode()).decode()
            return json.loads(s)
        except Exception as e:
            raise JWTError(str(e))
    fake_jwt.encode = _encode
    fake_jwt.decode = _decode
    fake_jose = types.ModuleType("jose")
    fake_jose.JWTError = JWTError
    fake_jose.jwt = fake_jwt
    sys.modules["jose"] = fake_jose

from app.main import app
from app.utils.jwt import get_current_user


class FakeInsertResult:
    def __init__(self, inserted_id):
        self.inserted_id = inserted_id


class FakeDeleteResult:
    def __init__(self, deleted_count: int):
        self.deleted_count = deleted_count


class FakeCollection:
    def __init__(self):
        self._docs = {}

    def _match(self, doc, query):
        if not query:
            return True
        # support simple queries and $or
        if "$or" in query:
            for cond in query["$or"]:
                if self._match(doc, cond):
                    return True
            return False
        for k, v in query.items():
            # allow ObjectId comparisons
            if k not in doc:
                return False
            if isinstance(v, ObjectId):
                if doc[k] != v:
                    return False
            else:
                if doc[k] != v:
                    return False
        return True

    def find_one(self, query=None):
        query = query or {}
        for d in self._docs.values():
            if self._match(d, query):
                return d
        return None

    def find(self, query=None):
        query = query or {}
        return [d for d in self._docs.values() if self._match(d, query)]

    def insert_one(self, doc: dict):
        # copy to avoid external mutation
        doc_copy = dict(doc)
        if "_id" in doc_copy:
            _id = doc_copy["_id"]
        else:
            _id = ObjectId()
            doc_copy["_id"] = _id
        self._docs[str(_id)] = doc_copy
        return FakeInsertResult(_id)

    def delete_one(self, query):
        for key, d in list(self._docs.items()):
            if self._match(d, query):
                del self._docs[key]
                return FakeDeleteResult(1)
        return FakeDeleteResult(0)

    def delete_many(self, query):
        removed = 0
        for key, d in list(self._docs.items()):
            if self._match(d, query):
                del self._docs[key]
                removed += 1
        return FakeDeleteResult(removed)

    def update_one(self, filter_query, update):
        for key, d in list(self._docs.items()):
            if self._match(d, filter_query):
                if "$set" in update:
                    d.update(update["$set"])
                self._docs[key] = d
                return


@pytest.fixture()
def client(tmp_path_factory, monkeypatch):
    # Replace MongoDB collections with in-memory fakes
    from app.config import database as db

    fake_user = FakeCollection()
    fake_analysis = FakeCollection()
    fake_statistics = FakeCollection()
    fake_timeseries = FakeCollection()

    monkeypatch.setattr(db, "user_collection", fake_user)
    monkeypatch.setattr(db, "analysis_collection", fake_analysis)
    monkeypatch.setattr(db, "statistics_collection", fake_statistics)
    monkeypatch.setattr(db, "timeseries_collection", fake_timeseries)

    # Also patch the already-imported names in route modules
    import app.routes.auth as auth_mod
    import app.routes.analysis as analysis_mod
    import app.routes.change_detection as cd_mod

    monkeypatch.setattr(auth_mod, "user_collection", fake_user)
    monkeypatch.setattr(analysis_mod, "analysis_collection", fake_analysis)
    monkeypatch.setattr(analysis_mod, "statistics_collection", fake_statistics)
    monkeypatch.setattr(cd_mod, "timeseries_collection", fake_timeseries)

    # Patch heavy utilities to return local test image and deterministic areas
    import app.utils.load_model as load_model_mod
    import app.utils.segmentation as segmentation_mod
    import app.utils.gee as gee_mod

    monkeypatch.setattr(load_model_mod, "_segment_image_from_url", lambda url: "/storage/sentinels/test_seg.png")
    monkeypatch.setattr(segmentation_mod, "_download_sentinel_image", lambda url: "/storage/sentinels/test_seg.png")
    monkeypatch.setattr(gee_mod, "get_region_area_m2", lambda region: 1000.0)

    # Patch names already imported into route modules
    monkeypatch.setattr(analysis_mod, "_segment_image_from_url", lambda url: "/storage/sentinels/test_seg.png")
    monkeypatch.setattr(analysis_mod, "_download_sentinel_image", lambda url: "/storage/sentinels/test_seg.png")
    monkeypatch.setattr(analysis_mod, "get_region_area_m2", lambda region: 1000.0)
    monkeypatch.setattr(analysis_mod, "decode_segmentation_url", segmentation_mod.decode_segmentation_url)

    monkeypatch.setattr(cd_mod, "_segment_image_from_url", lambda url: "/storage/sentinels/test_seg.png")
    monkeypatch.setattr(cd_mod, "decode_segmentation_url", segmentation_mod.decode_segmentation_url)
    monkeypatch.setattr(cd_mod, "get_region_area_m2", lambda region: 1000.0)

    # Create a default test user
    test_user_id = ObjectId()
    # store a hashed empty password so login with empty password succeeds
    import bcrypt as _bcrypt
    hashed_empty = _bcrypt.hashpw(b"", _bcrypt.gensalt()).decode("utf-8")
    fake_user.insert_one({
        "_id": test_user_id,
        "username": "testuser",
        "email": "test@example.com",
        "password": hashed_empty,
        "created_at": datetime.now(timezone.utc),
    })

    # Create storage sentinel image used by segmentation decoder
    storage_dir = os.path.join(os.getcwd(), "storage", "sentinels")
    os.makedirs(storage_dir, exist_ok=True)
    img_path = os.path.join(storage_dir, "test_seg.png")
    # 2x2 image with two colored pixels and two black pixels
    img = Image.new("RGB", (2, 2))
    img.putpixel((0, 0), (255, 255, 0))
    img.putpixel((1, 0), (0, 0, 0))
    img.putpixel((0, 1), (0, 0, 0))
    img.putpixel((1, 1), (0, 0, 255))
    img.save(img_path)

    # Insert one analysis doc referencing the test image
    analysis_doc = {
        "lat": 0.0,
        "lng": 0.0,
        "date": "2023-01-01",
        "cloud_cover": 10,
        "sentinel_url": "/storage/sentinels/test_seg.png",
        "segmentation_url": "/storage/sentinels/test_seg.png",
        "region_area_m2": 1000.0,
        "created_at": datetime.now(timezone.utc),
        "user_id": test_user_id,
    }
    result = fake_analysis.insert_one(analysis_doc)
    analysis_id = result.inserted_id

    # Insert a statistics doc linked to the analysis
    statistics_doc = {
        "_id": ObjectId(),
        "analysis_id": str(analysis_id),
        "created_at": datetime.now(timezone.utc),
        "image_size": {"width": 2, "height": 2},
        "total_pixels": 4,
        "unmatched_pixels": 2,
        "region_area_m2": 1000.0,
        "pixel_area_m2": 250.0,
        "classes": {},
        "user_id": test_user_id,
    }
    fake_statistics.insert_one(statistics_doc)

    # Insert a timeseries doc for change detection history
    timeseries_doc = {
        "_id": ObjectId(),
        "lat": 0.0,
        "lng": 0.0,
        "dates": ["2023-01-01"],
        "cloud_cover": 10,
        "user_id": test_user_id,
        "created_at": datetime.now(timezone.utc),
        "timeline": [],
    }
    fake_timeseries.insert_one(timeseries_doc)

    # Override dependency to bypass JWT validation in tests
    app.dependency_overrides[get_current_user] = lambda: {
        "sub": str(test_user_id),
        "username": "testuser",
        "email": "test@example.com",
    }

    client = TestClient(app)
    # attach some helpers
    client.test_user_id = test_user_id
    client.analysis_id = analysis_id

    yield client
