from __future__ import annotations

import csv
import io
import os
import sqlite3
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Annotated, Literal

from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlmodel import Field, Session, SQLModel, create_engine, select

SITE_ID = "pj-office"
DATA_PATH = Path(__file__).resolve().parent.parent / "rackscan.db"
engine = create_engine(f"sqlite:///{DATA_PATH}", connect_args={"check_same_thread": False})


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


class Site(SQLModel, table=True):
    id: str = Field(primary_key=True)
    client_name: str
    name: str
    created_at: str


class Device(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    site_id: str = Field(default=SITE_ID, index=True)
    name: str = Field(index=True)
    device_type: str
    brand: str | None = None
    model: str | None = None
    ip_address: str | None = None
    serial_number: str | None = None
    source: str = "Legacy device record"
    confidence: int = 0
    review_status: str = "verified"
    connection_summary: str | None = None


class EvidenceImport(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    site_id: str = Field(index=True)
    filename: str
    source: str
    raw_content: str
    observed_at: str
    imported_at: str
    row_count: int


class ProposedDevice(SQLModel, table=True):
    """Compatibility envelope for a parsed row; field evidence lives in Observation."""
    id: int | None = Field(default=None, primary_key=True)
    evidence_import_id: int = Field(index=True)
    row_number: int
    raw_row: str
    name: str
    device_type: str | None = None
    brand: str | None = None
    model: str | None = None
    ip_address: str | None = None
    serial_number: str | None = None
    source: str
    confidence: int
    observed_at: str
    review_status: str


class Observation(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    site_id: str = Field(index=True)
    device_id: int | None = Field(default=None, index=True)
    proposed_device_id: int | None = Field(default=None, index=True)
    field_name: str = Field(index=True)
    observed_value: str
    accepted_value_at_import: str | None = None
    evidence_import_id: int | None = Field(default=None, index=True)
    source: str
    confidence: int
    observed_at: str
    review_status: str = Field(default="pending", index=True)


class Connection(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    site_id: str = Field(index=True)
    device_a_id: int | None = Field(default=None, index=True)
    interface_a: str | None = None
    device_b_id: int | None = Field(default=None, index=True)
    interface_b: str | None = None
    relationship_type: str = "uplink"
    source: str
    evidence_import_id: int | None = Field(default=None, index=True)
    confidence: int
    observed_at: str
    review_status: str = "accepted"


class ReviewDecision(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    proposal_id: int | None = Field(default=None, index=True)
    observation_id: int | None = Field(default=None, index=True)
    connection_id: int | None = Field(default=None, index=True)
    decision: str
    decided_at: str
    note: str | None = None


class DeviceCreate(SQLModel):
    name: str = Field(min_length=1, max_length=80)
    device_type: str = Field(min_length=1, max_length=50)
    brand: str | None = Field(default=None, max_length=80)
    model: str | None = Field(default=None, max_length=80)
    ip_address: str | None = Field(default=None, max_length=45)
    serial_number: str | None = Field(default=None, max_length=100)


class ConnectionCreate(SQLModel):
    device_a_id: int | None = None
    interface_a: str | None = Field(default=None, max_length=80)
    device_b_id: int
    interface_b: str | None = Field(default=None, max_length=80)
    relationship_type: str = Field(default="uplink", max_length=50)
    observed_at: str | None = Field(default=None, max_length=64)


class ConnectionRead(SQLModel):
    id: int
    device_a_id: int | None
    device_a_name: str
    interface_a: str | None
    device_b_id: int
    device_b_name: str
    interface_b: str | None
    relationship_type: str
    source: str
    confidence: int
    observed_at: str


class CsvImportRequest(SQLModel):
    filename: str = Field(min_length=1, max_length=160)
    csv_text: str = Field(min_length=1, max_length=250_000)
    observed_at: str | None = Field(default=None, max_length=64)


class CliImportRequest(SQLModel):
    filename: str = Field(min_length=1, max_length=160)
    platform: str
    command: str
    cli_text: str = Field(min_length=1, max_length=250_000)
    observed_at: str | None = Field(default=None, max_length=64)


class ProposalDecisionRequest(SQLModel):
    note: str | None = Field(default=None, max_length=400)


class ObservationDecisionRequest(ProposalDecisionRequest):
    value: str | None = Field(default=None, max_length=400)


class EvidenceImportRead(SQLModel):
    id: int
    filename: str
    source: str
    observed_at: str
    imported_at: str
    row_count: int


class ProposedDeviceRead(SQLModel):
    id: int
    row_number: int
    raw_row: str
    name: str
    device_type: str | None
    brand: str | None
    model: str | None
    ip_address: str | None
    serial_number: str | None
    source: str
    confidence: int
    observed_at: str
    review_status: str


class CsvImportResponse(SQLModel):
    evidence_import: EvidenceImportRead
    proposals: list[ProposedDeviceRead]


class ReviewQueueItem(SQLModel):
    id: int
    kind: Literal["proposed_device", "field_observation", "field_conflict", "proposed_connection"]
    device_name: str
    field_name: str | None = None
    observed_value: str | None = None
    accepted_value: str | None = None
    source: str
    confidence: int
    observed_at: str
    status: str


class TopologyNode(SQLModel):
    id: str
    label: str
    kind: str
    device_id: int | None = None
    confidence: int
    source: str
    review_status: str = "verified"


class TopologyEdge(SQLModel):
    source: str
    target: str
    source_label: str
    confidence: int


class Topology(SQLModel):
    nodes: list[TopologyNode]
    edges: list[TopologyEdge]


class SiteSummary(SQLModel):
    site_id: str
    client_name: str
    site_name: str
    devices: int
    connections: int
    missing_fields: int
    conflicts: int
    status: str
    last_updated: str


class SiteResponse(SiteSummary):
    devices_list: list[Device]
    topology: Topology


CSV_FIELDS = {"name", "device_type", "brand", "model", "ip_address", "serial_number"}
DEVICE_FIELDS = ("device_type", "brand", "model", "ip_address", "serial_number")


def migrate_database() -> None:
    """Ordered SQLite upgrade which preserves the Phase 2 device table and data."""
    with sqlite3.connect(DATA_PATH) as connection:
        columns = {row[1] for row in connection.execute("PRAGMA table_info(device)")}
        if columns and "site_id" not in columns:
            connection.execute("ALTER TABLE device ADD COLUMN site_id TEXT NOT NULL DEFAULT 'pj-office'")
        decision_columns = {row[1] for row in connection.execute("PRAGMA table_info(reviewdecision)")}
        for column in ("observation_id", "connection_id"):
            if decision_columns and column not in decision_columns:
                connection.execute(f"ALTER TABLE reviewdecision ADD COLUMN {column} INTEGER")
        connection.execute("CREATE TABLE IF NOT EXISTS schema_migration (version INTEGER PRIMARY KEY, applied_at TEXT NOT NULL)")
        connection.commit()


def ensure_legacy_observations(session: Session) -> None:
    """Backfill summaries without fabricating timestamps unavailable in Phase 2."""
    for device in session.exec(select(Device).where(Device.site_id == SITE_ID)):
        if session.exec(select(Observation).where(Observation.device_id == device.id)).first():
            continue
        for field_name in DEVICE_FIELDS:
            value = getattr(device, field_name)
            if value is not None:
                session.add(Observation(site_id=SITE_ID, device_id=device.id, field_name=field_name, observed_value=value, accepted_value_at_import=value, source=f"Legacy migration: {device.source}", confidence=device.confidence, observed_at="unknown (migrated Phase 2 record)", review_status="accepted"))
    session.commit()


def seed_connections(session: Session) -> None:
    if session.exec(select(Connection).where(Connection.site_id == SITE_ID)).first():
        return
    by_name = {d.name: d for d in session.exec(select(Device).where(Device.site_id == SITE_ID))}
    for source, target, target_port, evidence, confidence in [(None, "FW-EDGE-01", "WAN", "Manual entry", 100), ("FW-EDGE-01", "CORE-SW01", "Port 1", "show system", 100), ("CORE-SW01", "ACCESS-SW01", "Port 24", "CSV inventory", 96), ("CORE-SW01", "ACCESS-SW02", "Port 23", "CLI text", 92), ("ACCESS-SW01", "AP-LOBBY", "Port 5", "LLDP", 88)]:
        target_device, source_device = by_name.get(target), by_name.get(source) if source else None
        if target_device:
            session.add(Connection(site_id=SITE_ID, device_a_id=source_device.id if source_device else None, device_b_id=target_device.id, interface_b=target_port, source=evidence, confidence=confidence, observed_at="unknown (migrated Phase 2 record)"))
    session.commit()


def create_db_and_seed() -> None:
    migrate_database()
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        if session.get(Site, SITE_ID) is None:
            session.add(Site(id=SITE_ID, client_name="ABC Sdn Bhd", name="Petaling Jaya Office", created_at=now()))
        if not session.exec(select(Device).where(Device.site_id == SITE_ID)).first():
            session.add_all([Device(name="CORE-SW01", device_type="Switch", brand="Aruba", model="2930F", ip_address="10.10.10.2", serial_number="CN4A2J0198", source="show system", confidence=100), Device(name="ACCESS-SW01", device_type="Switch", brand="HPE", model="1920-24G", ip_address="10.10.10.3", serial_number="CN73K90211", source="CSV inventory", confidence=96), Device(name="ACCESS-SW02", device_type="Switch", brand="HPE", model="1920-24G", ip_address="10.10.10.4", source="CLI text", confidence=92, review_status="review"), Device(name="FW-EDGE-01", device_type="Firewall", brand="Fortinet", model="FortiGate 60F", ip_address="10.10.10.1", serial_number="FGT60FTK2100X1AB", source="Manual entry", confidence=100), Device(name="AP-LOBBY", device_type="Access point", brand="Aruba", model="AP-515", ip_address="10.10.20.11", source="LLDP", confidence=88, review_status="review"), Device(name="AP-MEETING", device_type="Access point", brand="Unknown", source="Old spreadsheet", confidence=54, review_status="conflict")])
        session.commit(); ensure_legacy_observations(session); seed_connections(session)


@asynccontextmanager
async def lifespan(_: FastAPI):
    create_db_and_seed()
    yield


app = FastAPI(title="RackScan API", version="0.2.5", lifespan=lifespan)
cors_origins = os.getenv("RACKSCAN_CORS_ORIGINS", "http://localhost:3000,http://127.0.0.1:3000").split(",")
app.add_middleware(CORSMiddleware, allow_origins=[origin.strip() for origin in cors_origins if origin.strip()], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])


def get_session():
    with Session(engine) as session:
        yield session


SessionDep = Annotated[Session, Depends(get_session)]


def parse_csv_inventory(payload: CsvImportRequest) -> list[dict[str, str | None]]:
    reader = csv.DictReader(io.StringIO(payload.csv_text))
    if not reader.fieldnames or not {h.strip() for h in reader.fieldnames}.issuperset({"name"}):
        raise HTTPException(status_code=422, detail="CSV must include a name column.")
    headers = {header: header.strip() for header in reader.fieldnames}
    unknown = set(headers.values()) - CSV_FIELDS
    if unknown:
        raise HTTPException(status_code=422, detail=f"Unsupported CSV columns: {', '.join(sorted(unknown))}.")
    rows = []
    for row_number, row in enumerate(reader, start=2):
        values = {headers[key]: value.strip() if value and value.strip() else None for key, value in row.items() if key in headers}
        if not values.get("name"):
            raise HTTPException(status_code=422, detail=f"Row {row_number} needs a device name.")
        values["name"] = str(values["name"]).upper(); values["_row_number"] = str(row_number); rows.append(values)
    if not rows:
        raise HTTPException(status_code=422, detail="CSV contains no device rows.")
    return rows


def parse_arubaos_show_system(payload: CliImportRequest) -> list[dict[str, str | None]]:
    if payload.platform != "arubaos-switch" or payload.command != "show system":
        raise HTTPException(status_code=422, detail="Only ArubaOS-Switch 'show system' is supported in Phase 2.5.")
    fields = {key.strip().lower(): value.strip() for line in payload.cli_text.splitlines() if ":" in line for key, value in [line.split(":", 1)]}
    if not fields.get("system name"):
        raise HTTPException(status_code=422, detail="ArubaOS-Switch output needs a 'System Name' field.")
    description = fields.get("system description")
    return [{"name": fields["system name"].upper(), "device_type": "Switch", "brand": "Aruba", "model": description.removeprefix("Aruba ") if description else None, "ip_address": fields.get("ip address"), "serial_number": fields.get("serial number"), "_row_number": "1"}]


def proposal_read(item: ProposedDevice) -> ProposedDeviceRead:
    return ProposedDeviceRead.model_validate(item)


def import_read(item: EvidenceImport) -> EvidenceImportRead:
    return EvidenceImportRead.model_validate(item)


def proposal_status(session: Session, proposal_id: int) -> str:
    statuses = [item.review_status for item in session.exec(select(Observation).where(Observation.proposed_device_id == proposal_id))]
    return "conflict" if "conflict" in statuses else "review" if "pending" in statuses else "accepted" if statuses and all(status == "accepted" for status in statuses) else "rejected"


def persist_rows(session: Session, filename: str, source: str, raw_content: str, rows: list[dict[str, str | None]], observed_at: str) -> CsvImportResponse:
    evidence = EvidenceImport(site_id=SITE_ID, filename=filename, source=source, raw_content=raw_content, observed_at=observed_at, imported_at=now(), row_count=len(rows))
    session.add(evidence); session.commit(); session.refresh(evidence)
    proposals, confidence = [], 96 if source == "CSV inventory" else 92
    for row in rows:
        existing = session.exec(select(Device).where(Device.site_id == SITE_ID, Device.name == row["name"])).first()
        proposal = ProposedDevice(evidence_import_id=evidence.id, row_number=int(row["_row_number"] or 0), raw_row=" | ".join(f"{key}={value}" for key, value in row.items() if not key.startswith("_") and value is not None), name=str(row["name"]), device_type=row.get("device_type"), brand=row.get("brand"), model=row.get("model"), ip_address=row.get("ip_address"), serial_number=row.get("serial_number"), source=source, confidence=confidence, observed_at=observed_at, review_status="review")
        session.add(proposal); session.commit(); session.refresh(proposal); proposals.append(proposal)
        for field_name in DEVICE_FIELDS:
            value = row.get(field_name)
            if value is None: continue
            accepted = getattr(existing, field_name) if existing else None
            status = "accepted" if existing and accepted == value else "conflict" if existing and accepted else "pending"
            session.add(Observation(site_id=SITE_ID, device_id=existing.id if existing else None, proposed_device_id=proposal.id, field_name=field_name, observed_value=value, accepted_value_at_import=accepted, evidence_import_id=evidence.id, source=source, confidence=confidence, observed_at=observed_at, review_status=status))
        session.commit(); proposal.review_status = proposal_status(session, proposal.id); session.add(proposal); session.commit(); session.refresh(proposal)
    return CsvImportResponse(evidence_import=import_read(evidence), proposals=[proposal_read(item) for item in proposals])


def build_topology(session: Session, devices: list[Device]) -> Topology:
    nodes = [TopologyNode(id="internet", label="Internet", kind="External", confidence=100, source="Documented external endpoint")]
    by_id = {device.id: device for device in devices}
    for device in devices:
        evidence = session.exec(select(Observation).where(Observation.device_id == device.id, Observation.review_status == "accepted").order_by(Observation.id.desc())).first()
        nodes.append(TopologyNode(id=f"device-{device.id}", label=device.name, kind=device.device_type, device_id=device.id, confidence=evidence.confidence if evidence else device.confidence, source=evidence.source if evidence else device.source, review_status=device.review_status))
    edges = []
    for connection in session.exec(select(Connection).where(Connection.site_id == SITE_ID, Connection.review_status == "accepted")):
        target, source = by_id.get(connection.device_b_id), by_id.get(connection.device_a_id) if connection.device_a_id else None
        if target and (source or connection.device_a_id is None): edges.append(TopologyEdge(source=f"device-{source.id}" if source else "internet", target=f"device-{target.id}", source_label=connection.source, confidence=connection.confidence))
    return Topology(nodes=nodes, edges=edges)


def site_response(session: Session) -> SiteResponse:
    site = session.get(Site, SITE_ID)
    if not site: raise HTTPException(status_code=404, detail="Site not found.")
    devices = list(session.exec(select(Device).where(Device.site_id == SITE_ID).order_by(Device.name)))
    missing = sum(value is None or value == "Unknown" for device in devices for value in (device.brand, device.model, device.ip_address, device.serial_number))
    conflicts = len(list(session.exec(select(Observation).where(Observation.site_id == SITE_ID, Observation.review_status == "conflict"))))
    connections = len(list(session.exec(select(Connection).where(Connection.site_id == SITE_ID, Connection.review_status == "accepted"))))
    return SiteResponse(site_id=SITE_ID, client_name=site.client_name, site_name=site.name, devices=len(devices), connections=connections, missing_fields=missing, conflicts=conflicts, status="Survey in review", last_updated="Current local record", devices_list=devices, topology=build_topology(session, devices))


@app.get("/health")
def health() -> dict[str, str]: return {"status": "ok"}


@app.get("/api/sites/pj-office", response_model=SiteResponse)
def read_site(session: SessionDep) -> SiteResponse: return site_response(session)


@app.post("/api/sites/pj-office/devices", response_model=Device, status_code=201)
def create_device(payload: DeviceCreate, session: SessionDep) -> Device:
    name = payload.name.strip().upper()
    if session.exec(select(Device).where(Device.site_id == SITE_ID, Device.name == name)).first(): raise HTTPException(status_code=409, detail="A device with this name already exists.")
    device = Device(**payload.model_dump(), name=name, source="Manual entry", confidence=100); session.add(device); session.commit(); session.refresh(device)
    for field_name in DEVICE_FIELDS:
        value = getattr(device, field_name)
        if value: session.add(Observation(site_id=SITE_ID, device_id=device.id, field_name=field_name, observed_value=value, accepted_value_at_import=value, source="Manual entry", confidence=100, observed_at=now(), review_status="accepted"))
    session.commit(); return device


@app.get("/api/sites/pj-office/connections", response_model=list[ConnectionRead])
def read_connections(session: SessionDep) -> list[ConnectionRead]:
    devices = {device.id: device for device in session.exec(select(Device).where(Device.site_id == SITE_ID))}
    records = session.exec(select(Connection).where(Connection.site_id == SITE_ID, Connection.review_status == "accepted")).all()
    return [ConnectionRead(id=record.id, device_a_id=record.device_a_id, device_a_name=devices[record.device_a_id].name if record.device_a_id in devices else "Internet", interface_a=record.interface_a, device_b_id=record.device_b_id, device_b_name=devices[record.device_b_id].name, interface_b=record.interface_b, relationship_type=record.relationship_type, source=record.source, confidence=record.confidence, observed_at=record.observed_at) for record in records if record.device_b_id in devices]


@app.post("/api/sites/pj-office/connections", response_model=ConnectionRead, status_code=201)
def create_connection(payload: ConnectionCreate, session: SessionDep) -> ConnectionRead:
    if payload.device_a_id == payload.device_b_id:
        raise HTTPException(status_code=422, detail="A connection needs two distinct endpoints.")
    destination = session.get(Device, payload.device_b_id)
    source = session.get(Device, payload.device_a_id) if payload.device_a_id else None
    if not destination or destination.site_id != SITE_ID or (source and source.site_id != SITE_ID):
        raise HTTPException(status_code=422, detail="Choose devices from this site.")
    record = Connection(site_id=SITE_ID, device_a_id=source.id if source else None, interface_a=payload.interface_a or None, device_b_id=destination.id, interface_b=payload.interface_b or None, relationship_type=payload.relationship_type, source="Manual entry", confidence=100, observed_at=payload.observed_at or now())
    session.add(record); session.commit(); session.refresh(record)
    return ConnectionRead(id=record.id, device_a_id=record.device_a_id, device_a_name=source.name if source else "Internet", interface_a=record.interface_a, device_b_id=destination.id, device_b_name=destination.name, interface_b=record.interface_b, relationship_type=record.relationship_type, source=record.source, confidence=record.confidence, observed_at=record.observed_at)


@app.post("/api/sites/pj-office/evidence/csv", response_model=CsvImportResponse, status_code=201)
def import_csv_inventory(payload: CsvImportRequest, session: SessionDep) -> CsvImportResponse: return persist_rows(session, payload.filename, "CSV inventory", payload.csv_text, parse_csv_inventory(payload), payload.observed_at or now())


@app.post("/api/sites/pj-office/evidence/cli", response_model=CsvImportResponse, status_code=201)
def import_cli_text(payload: CliImportRequest, session: SessionDep) -> CsvImportResponse: return persist_rows(session, payload.filename, "ArubaOS-Switch show system", payload.cli_text, parse_arubaos_show_system(payload), payload.observed_at or now())


@app.get("/api/sites/pj-office/review-queue", response_model=list[ReviewQueueItem])
def read_review_queue(session: SessionDep) -> list[ReviewQueueItem]:
    items = []
    for observation in session.exec(select(Observation).where(Observation.site_id == SITE_ID, Observation.review_status.in_(["pending", "conflict"]))):
        proposal, device = session.get(ProposedDevice, observation.proposed_device_id) if observation.proposed_device_id else None, session.get(Device, observation.device_id) if observation.device_id else None
        items.append(ReviewQueueItem(id=observation.id, kind="field_conflict" if observation.review_status == "conflict" else "field_observation", device_name=device.name if device else proposal.name if proposal else "Unknown device", field_name=observation.field_name, observed_value=observation.observed_value, accepted_value=observation.accepted_value_at_import, source=observation.source, confidence=observation.confidence, observed_at=observation.observed_at, status=observation.review_status))
    return sorted(items, key=lambda item: (item.kind != "field_conflict", item.device_name, item.id))


def refresh_proposal(session: Session, proposal_id: int | None) -> None:
    if proposal_id is not None:
        proposal = session.get(ProposedDevice, proposal_id)
        if proposal: proposal.review_status = proposal_status(session, proposal_id); session.add(proposal)


@app.post("/api/sites/pj-office/observations/{observation_id}/accept", response_model=Observation)
def accept_observation(observation_id: int, payload: ObservationDecisionRequest, session: SessionDep) -> Observation:
    observation = session.get(Observation, observation_id)
    if not observation: raise HTTPException(status_code=404, detail="Observation not found.")
    if observation.review_status != "pending": raise HTTPException(status_code=409, detail="Only pending observations can be accepted; conflicts require explicit resolution.")
    device = session.get(Device, observation.device_id) if observation.device_id else None
    if device is None:
        proposal = session.get(ProposedDevice, observation.proposed_device_id)
        if not proposal: raise HTTPException(status_code=409, detail="Observation has no resolvable device.")
        device = session.exec(select(Device).where(Device.site_id == SITE_ID, Device.name == proposal.name)).first()
        if device is None: device = Device(site_id=SITE_ID, name=proposal.name, device_type=proposal.device_type or "Unknown", source=proposal.source, confidence=proposal.confidence); session.add(device); session.commit(); session.refresh(device)
        observation.device_id = device.id
    setattr(device, observation.field_name, payload.value or observation.observed_value); device.source, device.confidence, observation.review_status = observation.source, observation.confidence, "accepted"
    session.add_all([device, observation, ReviewDecision(proposal_id=observation.proposed_device_id, observation_id=observation.id, decision="accepted", decided_at=now(), note=payload.note)]); session.commit(); refresh_proposal(session, observation.proposed_device_id); session.commit(); session.refresh(observation); return observation


@app.post("/api/sites/pj-office/observations/{observation_id}/reject", response_model=Observation)
def reject_observation(observation_id: int, payload: ProposalDecisionRequest, session: SessionDep) -> Observation:
    observation = session.get(Observation, observation_id)
    if not observation or observation.review_status not in {"pending", "conflict"}: raise HTTPException(status_code=409, detail="Only unresolved observations can be rejected.")
    observation.review_status = "rejected"; session.add_all([observation, ReviewDecision(proposal_id=observation.proposed_device_id, observation_id=observation.id, decision="rejected", decided_at=now(), note=payload.note)]); session.commit(); refresh_proposal(session, observation.proposed_device_id); session.commit(); session.refresh(observation); return observation


@app.post("/api/sites/pj-office/observations/{observation_id}/resolve", response_model=Observation)
def resolve_conflict(observation_id: int, payload: ObservationDecisionRequest, session: SessionDep) -> Observation:
    observation = session.get(Observation, observation_id)
    if not observation or observation.review_status != "conflict": raise HTTPException(status_code=409, detail="Only a conflicting observation can be resolved.")
    device = session.get(Device, observation.device_id)
    if not device: raise HTTPException(status_code=409, detail="Conflict has no accepted device.")
    setattr(device, observation.field_name, payload.value or observation.observed_value); device.source, device.confidence, observation.review_status = observation.source, observation.confidence, "resolved"
    session.add_all([device, observation, ReviewDecision(proposal_id=observation.proposed_device_id, observation_id=observation.id, decision="resolved conflict", decided_at=now(), note=payload.note)]); session.commit(); refresh_proposal(session, observation.proposed_device_id); session.commit(); session.refresh(observation); return observation


@app.get("/api/sites/pj-office/evidence/imports/latest", response_model=CsvImportResponse | None)
def read_latest_import(session: SessionDep) -> CsvImportResponse | None:
    evidence = session.exec(select(EvidenceImport).where(EvidenceImport.site_id == SITE_ID).order_by(EvidenceImport.id.desc())).first()
    if not evidence: return None
    proposals = list(session.exec(select(ProposedDevice).where(ProposedDevice.evidence_import_id == evidence.id).order_by(ProposedDevice.row_number)))
    return CsvImportResponse(evidence_import=import_read(evidence), proposals=[proposal_read(item) for item in proposals])
