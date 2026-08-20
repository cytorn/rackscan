import sqlite3
from pathlib import Path
from uuid import uuid4

from fastapi.testclient import TestClient
from fastapi import HTTPException
import pytest
from sqlmodel import Session, create_engine, select

import app.main as rackscan
from app.main import CliImportRequest, Observation, app, parse_arubaos_show_system


FIXTURES = Path(__file__).parent / "fixtures" / "aruba_aos_switch" / "show_system"


@pytest.fixture(autouse=True)
def isolated_database(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    database = tmp_path / "rackscan.db"
    monkeypatch.setattr(rackscan, "DATA_PATH", database)
    monkeypatch.setattr(rackscan, "engine", create_engine(f"sqlite:///{database}", connect_args={"check_same_thread": False}))


def import_csv(client: TestClient, name: str, row: str) -> dict:
    response = client.post(
        "/api/sites/pj-office/evidence/csv",
        json={"filename": f"{name}.csv", "csv_text": row, "observed_at": "2026-08-18T08:00:00Z"},
    )
    assert response.status_code == 201, response.text
    return response.json()


def test_seeded_site_migrates_to_persisted_connections_and_observations() -> None:
    with TestClient(app) as client:
        site = client.get("/api/sites/pj-office")
    assert site.status_code == 200
    body = site.json()
    assert body["client_name"] == "ABC Sdn Bhd"
    assert body["connections"] >= 5
    assert any(edge["source"] == "internet" for edge in body["topology"]["edges"])
    assert not any(node["label"] == "AP-MEETING" and any(edge["target"] == node["id"] for edge in body["topology"]["edges"]) for node in body["topology"]["nodes"])


def test_migration_preserves_phase_2_device_and_marks_unknown_observed_time() -> None:
    with sqlite3.connect(rackscan.DATA_PATH) as connection:
        connection.execute("CREATE TABLE device (id INTEGER PRIMARY KEY, name TEXT NOT NULL, device_type TEXT NOT NULL, brand TEXT, model TEXT, ip_address TEXT, serial_number TEXT, source TEXT NOT NULL, confidence INTEGER NOT NULL, review_status TEXT NOT NULL, connection_summary TEXT)")
        connection.execute("INSERT INTO device VALUES (1, 'OLD-SW01', 'Switch', 'Aruba', NULL, NULL, 'OLD-123', 'CSV inventory', 96, 'verified', NULL)")
    with TestClient(app):
        with Session(rackscan.engine) as session:
            observation = session.exec(select(Observation).where(Observation.device_id == 1, Observation.field_name == "serial_number")).one()
    assert observation.observed_value == "OLD-123"
    assert observation.observed_at == "unknown (migrated Phase 2 record)"


def test_device_creation_requires_unique_name_and_records_manual_observations() -> None:
    with TestClient(app) as client:
        duplicate = client.post("/api/sites/pj-office/devices", json={"name": "core-sw01", "device_type": "Switch"})
    assert duplicate.status_code == 409


def test_manual_connection_is_persisted_and_returned_to_topology() -> None:
    with TestClient(app) as client:
        site = client.get("/api/sites/pj-office").json()
        devices = {device["name"]: device["id"] for device in site["devices_list"]}
        created = client.post("/api/sites/pj-office/connections", json={"device_a_id": devices["CORE-SW01"], "interface_a": "Port 10", "device_b_id": devices["AP-MEETING"], "interface_b": "eth0"})
        connections = client.get("/api/sites/pj-office/connections").json()
        topology = client.get("/api/sites/pj-office").json()["topology"]
    assert created.status_code == 201
    assert any(link["device_b_name"] == "AP-MEETING" for link in connections)
    ap_node = next(node["id"] for node in topology["nodes"] if node["label"] == "AP-MEETING")
    assert any(edge["target"] == ap_node for edge in topology["edges"])


def test_pending_observation_accept_updates_resolved_device_and_preserves_queue_history() -> None:
    name = f"NEW-SWITCH-{uuid4().hex[:8]}".upper()
    with TestClient(app) as client:
        import_csv(client, "new-device", f"name,device_type,brand,serial_number\n{name},Switch,Aruba,CN-NEW\n")
        queue = client.get("/api/sites/pj-office/review-queue").json()
        pending = next(item for item in queue if item["device_name"] == name and item["field_name"] == "device_type")
        accepted = client.post(f"/api/sites/pj-office/observations/{pending['id']}/accept", json={})
        site = client.get("/api/sites/pj-office").json()
    assert accepted.status_code == 200
    assert accepted.json()["review_status"] == "accepted"
    assert any(device["name"] == name and device["device_type"] == "Switch" for device in site["devices_list"])


def test_conflicting_observation_never_silently_overwrites_and_can_be_resolved() -> None:
    conflicting_serial = f"CONFLICT-{uuid4().hex[:8]}".upper()
    with TestClient(app) as client:
        import_csv(client, "conflict", f"name,device_type,serial_number\nCORE-SW01,Switch,{conflicting_serial}\n")
        queue = client.get("/api/sites/pj-office/review-queue").json()
        conflict = next(item for item in queue if item["device_name"] == "CORE-SW01" and item["field_name"] == "serial_number" and item["observed_value"] == conflicting_serial)
        blocked = client.post(f"/api/sites/pj-office/observations/{conflict['id']}/accept", json={})
        before = next(device for device in client.get("/api/sites/pj-office").json()["devices_list"] if device["name"] == "CORE-SW01")
        resolved = client.post(f"/api/sites/pj-office/observations/{conflict['id']}/resolve", json={})
        after = next(device for device in client.get("/api/sites/pj-office").json()["devices_list"] if device["name"] == "CORE-SW01")
    assert blocked.status_code == 409
    assert before["serial_number"] != conflicting_serial
    assert resolved.status_code == 200
    assert resolved.json()["review_status"] == "resolved"
    assert after["serial_number"] == conflicting_serial


def test_rejecting_observation_removes_it_from_the_site_wide_queue() -> None:
    name = f"REJECT-{uuid4().hex[:8]}".upper()
    with TestClient(app) as client:
        import_csv(client, "reject", f"name,device_type\n{name},Switch\n")
        item = next(item for item in client.get("/api/sites/pj-office/review-queue").json() if item["device_name"] == name)
        rejected = client.post(f"/api/sites/pj-office/observations/{item['id']}/reject", json={})
        queue = client.get("/api/sites/pj-office/review-queue").json()
    assert rejected.status_code == 200
    assert not any(item["device_name"] == name for item in queue)


def test_aruba_parser_fixtures_preserve_missing_values_and_accept_formatting_variation() -> None:
    normal = parse_arubaos_show_system(CliImportRequest(filename="normal.txt", platform="arubaos-switch", command="show system", cli_text=(FIXTURES / "sample_01.txt").read_text()))[0]
    missing = parse_arubaos_show_system(CliImportRequest(filename="missing.txt", platform="arubaos-switch", command="show system", cli_text=(FIXTURES / "missing_serial.txt").read_text()))[0]
    varied = parse_arubaos_show_system(CliImportRequest(filename="varied.txt", platform="arubaos-switch", command="show system", cli_text=(FIXTURES / "formatting_variation.txt").read_text()))[0]
    assert normal["serial_number"] == "CN123456"
    assert missing["serial_number"] is None
    assert varied["name"] == "ACCESS-SW05"


def test_incomplete_aruba_fixture_fails_safely() -> None:
    try:
        parse_arubaos_show_system(CliImportRequest(filename="bad.txt", platform="arubaos-switch", command="show system", cli_text=(FIXTURES / "incomplete_output.txt").read_text()))
    except HTTPException as error:
        assert error.status_code == 422
    else:
        raise AssertionError("Incomplete output should require a System Name.")
