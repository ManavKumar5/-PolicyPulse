import json
from app import app


def test_scan_endpoint():
    client = app.test_client()
    resp = client.post(
        "/scan", json={"text": "Email me at a@b.com. This is confidential."}
    )
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["flags_found"] >= 1
    assert "scanId" in data


def test_reports_flow():
    client = app.test_client()
    resp = client.post("/scan", json={"text": "Please share credentials."})
    sid = resp.get_json()["scanId"]
    rep = client.get(f"/reports/{sid}")
    assert rep.status_code == 200
    js = rep.get_json()
    assert js["id"] == sid
