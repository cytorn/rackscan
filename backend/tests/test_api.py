from fastapi.testclient import TestClient
from uuid import uuid4

from app.main import app


def test_seeded_site_is_available() -> None:
    with TestClient(app) as client:
        response = client.get("/api/sites/pj-office")
    assert response.status_code == 200
    body = response.json()
    assert body["client_name"] == "ABC Sdn Bhd"
    assert body["devices"] >= 6
    assert any(device["name"] == "CORE-SW01" for device in body["devices_list"])
    assert any(edge["source"] == "internet" for edge in body["topology"]["edges"])
    assert not any(edge["target"] == next(node["id"] for node in body["topology"]["nodes"] if node["label"] == "AP-MEETING") for edge in body["topology"]["edges"])


def test_device_creation_requires_unique_name() -> None:
    with TestClient(app) as client:
        duplicate = client.post("/api/sites/pj-office/devices", json={"name": "core-sw01", "device_type": "Switch"})
    assert duplicate.status_code == 409


def test_csv_import_retains_rows_and_flags_existing_device() -> None:
    csv_text = "name,device_type,brand,ip_address\nCORE-SW01,Switch,Aruba,10.10.10.2\nNEW-AP,Access point,Aruba,10.10.20.99\n"
    with TestClient(app) as client:
        response = client.post("/api/sites/pj-office/evidence/csv", json={"filename": "survey.csv", "csv_text": csv_text, "observed_at": "2026-08-18T08:00:00Z"})
    assert response.status_code == 201
    body = response.json()
    assert body["evidence_import"]["row_count"] == 2
    assert body["proposals"][0]["review_status"] == "conflict"
    assert body["proposals"][0]["raw_row"] == "name=CORE-SW01 | device_type=Switch | brand=Aruba | ip_address=10.10.10.2"
    assert body["proposals"][1]["review_status"] == "review"
    with TestClient(app) as client:
        latest = client.get("/api/sites/pj-office/evidence/imports/latest")
    assert latest.status_code == 200
    assert latest.json()["evidence_import"]["filename"] == "survey.csv"


def test_review_accepts_new_csv_proposal_without_overwriting_existing_device() -> None:
    name = f"NEW-SWITCH-{uuid4().hex[:8]}".upper()
    with TestClient(app) as client:
        imported = client.post("/api/sites/pj-office/evidence/csv", json={"filename": "new.csv", "csv_text": f"name,device_type\n{name},Switch\n"}).json()
        accepted = client.post(f"/api/sites/pj-office/evidence/proposals/{imported['proposals'][0]['id']}/accept", json={})
        site = client.get("/api/sites/pj-office").json()
    assert accepted.status_code == 200
    assert accepted.json()["review_status"] == "accepted"
    assert any(device["name"] == name and device["source"] == "CSV inventory" for device in site["devices_list"])


def test_aruba_show_system_parser_creates_reviewable_proposal() -> None:
    cli_text = "System Name : ACCESS-SW03\nSystem Description : Aruba 2930F 24G PoEP\nSerial Number : CN123456\nIP Address : 10.10.10.5\n"
    with TestClient(app) as client:
        response = client.post("/api/sites/pj-office/evidence/cli", json={"filename": "access-sw03.txt", "platform": "arubaos-switch", "command": "show system", "cli_text": cli_text})
    assert response.status_code == 201
    proposal = response.json()["proposals"][0]
    assert proposal["name"] == "ACCESS-SW03"
    assert proposal["source"] == "ArubaOS-Switch show system"
    assert proposal["review_status"] == "review"
