"""Tests for the ClawGuard FastAPI application."""

import zipfile
from io import BytesIO

from fastapi.testclient import TestClient

from clawguard.api.app import _scan_ids, _scan_store, app


def _reset_store():
    """Clear the in-memory scan store between tests."""
    _scan_store.clear()
    _scan_ids.clear()


class TestHealthEndpoint:
    def test_health(self):
        client = TestClient(app)
        response = client.get("/api/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert "version" in data


class TestScanEndpoint:
    def setup_method(self):
        _reset_store()

    def test_scan_local_path(self, fixtures_dir):
        client = TestClient(app)
        response = client.post(
            "/api/scan",
            json={"path": str(fixtures_dir / "clean_skill")},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "completed"
        assert data["scan_id"]
        assert data["result"]["skill"]["name"] == "github"
        assert data["result"]["score"]["recommendation"] == "PASS"

    def test_scan_malicious_skill(self, fixtures_dir):
        client = TestClient(app)
        response = client.post(
            "/api/scan",
            json={"path": str(fixtures_dir / "malicious_credential_harvester")},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["result"]["score"]["score"] < 80

    def test_scan_no_url_or_path(self):
        client = TestClient(app)
        response = client.post("/api/scan", json={})
        assert response.status_code == 400

    def test_scan_invalid_path(self):
        client = TestClient(app)
        response = client.post(
            "/api/scan",
            json={"path": "/nonexistent/path"},
        )
        assert response.status_code == 422


class TestUploadEndpoint:
    def setup_method(self):
        _reset_store()

    def test_upload_valid_zip(self, fixtures_dir):
        buf = BytesIO()
        skill_dir = fixtures_dir / "clean_skill"
        with zipfile.ZipFile(buf, "w") as zf:
            for f in skill_dir.rglob("*"):
                if f.is_file():
                    zf.write(f, f.relative_to(skill_dir))
        buf.seek(0)

        client = TestClient(app)
        response = client.post(
            "/api/scan/upload",
            files={"file": ("skill.zip", buf, "application/zip")},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["result"]["skill"]["name"] == "github"

    def test_upload_invalid_zip(self):
        client = TestClient(app)
        response = client.post(
            "/api/scan/upload",
            files={"file": ("bad.zip", BytesIO(b"not a zip"), "application/zip")},
        )
        assert response.status_code == 400

    def test_upload_no_skill_md(self):
        buf = BytesIO()
        with zipfile.ZipFile(buf, "w") as zf:
            zf.writestr("README.md", "no skill here")
        buf.seek(0)

        client = TestClient(app)
        response = client.post(
            "/api/scan/upload",
            files={"file": ("skill.zip", buf, "application/zip")},
        )
        assert response.status_code == 400


class TestGetScanEndpoint:
    def setup_method(self):
        _reset_store()

    def test_get_scan_exists(self, fixtures_dir):
        client = TestClient(app)
        # First create a scan
        post_resp = client.post(
            "/api/scan",
            json={"path": str(fixtures_dir / "clean_skill")},
        )
        scan_id = post_resp.json()["scan_id"]

        # Then retrieve it
        response = client.get(f"/api/scan/{scan_id}")
        assert response.status_code == 200
        data = response.json()
        assert data["scan_id"] == scan_id
        assert data["skill"]["name"] == "github"

    def test_get_scan_not_found(self):
        client = TestClient(app)
        response = client.get("/api/scan/nonexistent-id")
        assert response.status_code == 404


class TestListScansEndpoint:
    def setup_method(self):
        _reset_store()

    def test_list_empty(self):
        client = TestClient(app)
        response = client.get("/api/scans")
        assert response.status_code == 200
        assert response.json() == []

    def test_list_with_scans(self, fixtures_dir):
        client = TestClient(app)
        # Create two scans
        client.post("/api/scan", json={"path": str(fixtures_dir / "clean_skill")})
        client.post(
            "/api/scan",
            json={"path": str(fixtures_dir / "malicious_credential_harvester")},
        )

        response = client.get("/api/scans")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2
        # Newest first
        assert "scan_id" in data[0]
        assert "skill_name" in data[0]

    def test_list_pagination(self, fixtures_dir):
        client = TestClient(app)
        # Create 3 scans
        for fixture in ["clean_skill", "typosquat_skill", "obfuscated_payload"]:
            client.post(
                "/api/scan",
                json={"path": str(fixtures_dir / fixture)},
            )

        response = client.get("/api/scans?limit=2&offset=0")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2

        response2 = client.get("/api/scans?limit=2&offset=2")
        data2 = response2.json()
        assert len(data2) == 1


class TestErrorResponses:
    def test_404_consistent_shape(self):
        client = TestClient(app)
        response = client.get("/api/scan/missing-id")
        assert response.status_code == 404
        data = response.json()
        assert "detail" in data
