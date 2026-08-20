from __future__ import annotations

import csv
import io
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Annotated

from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlmodel import Field, Session, SQLModel, create_engine, select


class Device(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    name: str = Field(index=True)
    device_type: str
    brand: str | None = None
    model: str | None = None
    ip_address: str | None = None
    serial_number: str | None = None
    source: str = "Manual entry"
    confidence: int = 100
    review_status: str = "verified"
    connection_summary: str | None = None


class DeviceCreate(SQLModel):
    name: str = Field(min_length=1, max_length=80)
    device_type: str = Field(min_length=1, max_length=50)
    brand: str | None = Field(default=None, max_length=80)
    model: str | None = Field(default=None, max_length=80)
    ip_address: str | None = Field(default=None, max_length=45)
    serial_number: str | None = Field(default=None, max_length=100)


class EvidenceImport(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    site_id: str = Field(index=True)
    filename: str
    source: str = "CSV inventory"
    raw_content: str
    observed_at: str
    imported_at: str
    row_count: int


class ProposedDevice(SQLModel, table=True):
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


class ReviewDecision(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    proposal_id: int = Field(index=True)
    decision: str
    decided_at: str
    note: str | None = None


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


class ProposalEdit(SQLModel):
    name: str | None = Field(default=None, min_length=1, max_length=80)
    device_type: str | None = Field(default=None, max_length=50)
    brand: str | None = Field(default=None, max_length=80)
    model: str | None = Field(default=None, max_length=80)
    ip_address: str | None = Field(default=None, max_length=45)
    serial_number: str | None = Field(default=None, max_length=100)


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
    topology: "Topology"


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


DATA_PATH = Path(__file__).resolve().parent.parent / "rackscan.db"
engine = create_engine(f"sqlite:///{DATA_PATH}", connect_args={"check_same_thread": False})

SEED_DEVICES = [
    Device(name="CORE-SW01", device_type="Switch", brand="Aruba", model="2930F", ip_address="10.10.10.2", serial_number="CN4A2J0198", source="show system", confidence=100, connection_summary="Uplinks to 3 access switches"),
    Device(name="ACCESS-SW01", device_type="Switch", brand="HPE", model="1920-24G", ip_address="10.10.10.3", serial_number="CN73K90211", source="CSV inventory", confidence=96, connection_summary="CORE-SW01 · Port 24"),
    Device(name="ACCESS-SW02", device_type="Switch", brand="HPE", model="1920-24G", ip_address="10.10.10.4", source="CLI text", confidence=92, review_status="review", connection_summary="CORE-SW01 · Port 23"),
    Device(name="FW-EDGE-01", device_type="Firewall", brand="Fortinet", model="FortiGate 60F", ip_address="10.10.10.1", serial_number="FGT60FTK2100X1AB", source="Manual entry", confidence=100, connection_summary="Internet ↔ CORE-SW01"),
    Device(name="AP-LOBBY", device_type="Access point", brand="Aruba", model="AP-515", ip_address="10.10.20.11", source="LLDP", confidence=88, review_status="review", connection_summary="ACCESS-SW01 · Port 5"),
    Device(name="AP-MEETING", device_type="Access point", brand="Unknown", source="Old spreadsheet", confidence=54, review_status="conflict", connection_summary="Connection differs from observed LLDP"),
]


def create_db_and_seed() -> None:
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        if session.exec(select(Device)).first() is None:
            session.add_all(SEED_DEVICES)
            session.commit()


@asynccontextmanager
async def lifespan(_: FastAPI):
    create_db_and_seed()
    yield


app = FastAPI(title="RackScan API", version="0.1.0", lifespan=lifespan)
app.add_middleware(CORSMiddleware, allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])


def get_session():
    with Session(engine) as session:
        yield session


SessionDep = Annotated[Session, Depends(get_session)]


def site_summary(devices: list[Device]) -> SiteSummary:
    missing_fields = sum(field is None or field == "Unknown" for device in devices for field in (device.brand, device.model, device.ip_address, device.serial_number))
    return SiteSummary(site_id="pj-office", client_name="ABC Sdn Bhd", site_name="Petaling Jaya Office", devices=len(devices), connections=7, missing_fields=missing_fields, conflicts=sum(device.review_status == "conflict" for device in devices), status="Survey in review", last_updated="Today, 10:42 AM")


def build_topology(devices: list[Device]) -> Topology:
    """Build only relationships supported by the current evidence set.

    A device with a conflict is retained as an unresolved node instead of being
    placed on a link. This makes absence of trustworthy relationship evidence
    visible to the reviewer.
    """
    by_name = {device.name: device for device in devices}
    nodes = [
        TopologyNode(
            id="internet",
            label="Internet",
            kind="External",
            confidence=100,
            source="Manual entry",
        )
    ]
    for device in devices:
        nodes.append(
            TopologyNode(
                id=f"device-{device.id}",
                label=device.name,
                kind=device.device_type,
                device_id=device.id,
                confidence=device.confidence,
                source=device.source,
                review_status=device.review_status,
            )
        )

    def node_id(name: str) -> str | None:
        device = by_name.get(name)
        return f"device-{device.id}" if device and device.id is not None else None

    declared_edges = [
        ("internet", "FW-EDGE-01", "Manual entry", 100),
        ("FW-EDGE-01", "CORE-SW01", "show system", 100),
        ("CORE-SW01", "ACCESS-SW01", "CSV inventory", 96),
        ("CORE-SW01", "ACCESS-SW02", "CLI text", 92),
        ("ACCESS-SW01", "AP-LOBBY", "LLDP", 88),
    ]
    edges = []
    for source, target, source_label, confidence in declared_edges:
        resolved_source = source if source == "internet" else node_id(source)
        resolved_target = node_id(target)
        if resolved_source and resolved_target:
            edges.append(TopologyEdge(source=resolved_source, target=resolved_target, source_label=source_label, confidence=confidence))
    return Topology(nodes=nodes, edges=edges)


CSV_FIELDS = {"name", "device_type", "brand", "model", "ip_address", "serial_number"}


def parse_csv_inventory(payload: CsvImportRequest, devices: list[Device]) -> list[dict[str, str | None]]:
    reader = csv.DictReader(io.StringIO(payload.csv_text))
    if not reader.fieldnames or not {header.strip() for header in reader.fieldnames}.issuperset({"name"}):
        raise HTTPException(status_code=422, detail="CSV must include a name column.")
    normalized_headers = {header: header.strip() for header in reader.fieldnames}
    unknown_headers = set(normalized_headers.values()) - CSV_FIELDS
    if unknown_headers:
        raise HTTPException(status_code=422, detail=f"Unsupported CSV columns: {', '.join(sorted(unknown_headers))}.")
    parsed: list[dict[str, str | None]] = []
    existing_names = {device.name for device in devices}
    seen_names: set[str] = set()
    for row_number, row in enumerate(reader, start=2):
        values = {normalized_headers[key]: (value.strip() if value and value.strip() else None) for key, value in row.items() if key in normalized_headers}
        name = values.get("name")
        if not name:
            raise HTTPException(status_code=422, detail=f"Row {row_number} needs a device name.")
        values["name"] = name.upper()
        values["_row_number"] = str(row_number)
        values["_status"] = "review" if name.upper() in seen_names or name.upper() not in existing_names else "conflict"
        seen_names.add(name.upper())
        parsed.append(values)
    if not parsed:
        raise HTTPException(status_code=422, detail="CSV contains no device rows.")
    return parsed


def parse_arubaos_show_system(payload: CliImportRequest, devices: list[Device]) -> list[dict[str, str | None]]:
    if payload.platform != "arubaos-switch" or payload.command != "show system":
        raise HTTPException(status_code=422, detail="Only ArubaOS-Switch 'show system' is supported in Phase 2.")
    fields = {key.strip().lower(): value.strip() for line in payload.cli_text.splitlines() if ":" in line for key, value in [line.split(":", 1)]}
    name = fields.get("system name")
    if not name:
        raise HTTPException(status_code=422, detail="ArubaOS-Switch output needs a 'System Name' field.")
    description = fields.get("system description")
    model = description.removeprefix("Aruba ") if description else None
    existing_names = {device.name for device in devices}
    normalized_name = name.upper()
    return [{"name": normalized_name, "device_type": "Switch", "brand": "Aruba", "model": model, "ip_address": fields.get("ip address"), "serial_number": fields.get("serial number"), "_row_number": "1", "_status": "conflict" if normalized_name in existing_names else "review"}]


def to_import_response(evidence_import: EvidenceImport, proposals: list[ProposedDevice]) -> CsvImportResponse:
    return CsvImportResponse(evidence_import=EvidenceImportRead(id=evidence_import.id, filename=evidence_import.filename, source=evidence_import.source, observed_at=evidence_import.observed_at, imported_at=evidence_import.imported_at, row_count=evidence_import.row_count), proposals=[ProposedDeviceRead(id=proposal.id, row_number=proposal.row_number, raw_row=proposal.raw_row, name=proposal.name, device_type=proposal.device_type, brand=proposal.brand, model=proposal.model, ip_address=proposal.ip_address, serial_number=proposal.serial_number, source=proposal.source, confidence=proposal.confidence, observed_at=proposal.observed_at, review_status=proposal.review_status) for proposal in proposals])


def persist_proposals(session: Session, filename: str, source: str, raw_content: str, parsed_rows: list[dict[str, str | None]], observed_at: str) -> CsvImportResponse:
    evidence_import = EvidenceImport(site_id="pj-office", filename=filename, source=source, raw_content=raw_content, observed_at=observed_at, imported_at=datetime.now(timezone.utc).isoformat(), row_count=len(parsed_rows))
    session.add(evidence_import); session.commit(); session.refresh(evidence_import)
    proposals = [ProposedDevice(evidence_import_id=evidence_import.id, row_number=int(row["_row_number"] or 0), raw_row=" | ".join(f"{key}={value}" for key, value in row.items() if not key.startswith("_")), name=str(row["name"]), device_type=row.get("device_type"), brand=row.get("brand"), model=row.get("model"), ip_address=row.get("ip_address"), serial_number=row.get("serial_number"), source=source, confidence=96 if source == "CSV inventory" else 92, observed_at=observed_at, review_status=str(row["_status"])) for row in parsed_rows]
    session.add_all(proposals); session.commit()
    return to_import_response(evidence_import, proposals)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/api/sites/pj-office", response_model=SiteResponse)
def read_site(session: SessionDep) -> SiteResponse:
    devices = list(session.exec(select(Device).order_by(Device.name)))
    return SiteResponse(**site_summary(devices).model_dump(), devices_list=devices, topology=build_topology(devices))


@app.post("/api/sites/pj-office/devices", response_model=Device, status_code=201)
def create_device(payload: DeviceCreate, session: SessionDep) -> Device:
    normalized_name = payload.name.strip().upper()
    existing = session.exec(select(Device).where(Device.name == normalized_name)).first()
    if existing:
        raise HTTPException(status_code=409, detail="A device with this name already exists.")
    device = Device(**payload.model_dump(), name=normalized_name)
    session.add(device)
    session.commit()
    session.refresh(device)
    return device


@app.post("/api/sites/pj-office/evidence/csv", response_model=CsvImportResponse, status_code=201)
def import_csv_inventory(payload: CsvImportRequest, session: SessionDep) -> CsvImportResponse:
    devices = list(session.exec(select(Device)))
    parsed_rows = parse_csv_inventory(payload, devices)
    observed_at = payload.observed_at or datetime.now(timezone.utc).isoformat()
    return persist_proposals(session, payload.filename, "CSV inventory", payload.csv_text, parsed_rows, observed_at)


@app.post("/api/sites/pj-office/evidence/cli", response_model=CsvImportResponse, status_code=201)
def import_cli_text(payload: CliImportRequest, session: SessionDep) -> CsvImportResponse:
    parsed_rows = parse_arubaos_show_system(payload, list(session.exec(select(Device))))
    observed_at = payload.observed_at or datetime.now(timezone.utc).isoformat()
    return persist_proposals(session, payload.filename, "ArubaOS-Switch show system", payload.cli_text, parsed_rows, observed_at)


@app.post("/api/sites/pj-office/evidence/proposals/{proposal_id}/accept", response_model=ProposedDeviceRead)
def accept_proposal(proposal_id: int, payload: ProposalDecisionRequest, session: SessionDep) -> ProposedDeviceRead:
    proposal = session.get(ProposedDevice, proposal_id)
    if proposal is None: raise HTTPException(status_code=404, detail="Proposal not found.")
    if proposal.review_status == "conflict": raise HTTPException(status_code=409, detail="Conflicting evidence must be corrected or rejected before acceptance.")
    if proposal.review_status != "review": raise HTTPException(status_code=409, detail="Only pending proposals can be accepted.")
    if session.exec(select(Device).where(Device.name == proposal.name)).first(): raise HTTPException(status_code=409, detail="A device with this name already exists.")
    device = Device(name=proposal.name, device_type=proposal.device_type or "Unknown", brand=proposal.brand, model=proposal.model, ip_address=proposal.ip_address, serial_number=proposal.serial_number, source=proposal.source, confidence=proposal.confidence, review_status="verified")
    proposal.review_status = "accepted"; session.add(device); session.add(proposal); session.add(ReviewDecision(proposal_id=proposal_id, decision="accepted", decided_at=datetime.now(timezone.utc).isoformat(), note=payload.note)); session.commit(); session.refresh(proposal)
    return ProposedDeviceRead(id=proposal.id, row_number=proposal.row_number, raw_row=proposal.raw_row, name=proposal.name, device_type=proposal.device_type, brand=proposal.brand, model=proposal.model, ip_address=proposal.ip_address, serial_number=proposal.serial_number, source=proposal.source, confidence=proposal.confidence, observed_at=proposal.observed_at, review_status=proposal.review_status)


@app.post("/api/sites/pj-office/evidence/proposals/{proposal_id}/reject", response_model=ProposedDeviceRead)
def reject_proposal(proposal_id: int, payload: ProposalDecisionRequest, session: SessionDep) -> ProposedDeviceRead:
    proposal = session.get(ProposedDevice, proposal_id)
    if proposal is None: raise HTTPException(status_code=404, detail="Proposal not found.")
    if proposal.review_status in {"accepted", "rejected"}: raise HTTPException(status_code=409, detail="This proposal has already been decided.")
    proposal.review_status = "rejected"; session.add(proposal); session.add(ReviewDecision(proposal_id=proposal_id, decision="rejected", decided_at=datetime.now(timezone.utc).isoformat(), note=payload.note)); session.commit(); session.refresh(proposal)
    return ProposedDeviceRead(id=proposal.id, row_number=proposal.row_number, raw_row=proposal.raw_row, name=proposal.name, device_type=proposal.device_type, brand=proposal.brand, model=proposal.model, ip_address=proposal.ip_address, serial_number=proposal.serial_number, source=proposal.source, confidence=proposal.confidence, observed_at=proposal.observed_at, review_status=proposal.review_status)


@app.get("/api/sites/pj-office/evidence/imports/latest", response_model=CsvImportResponse | None)
def read_latest_csv_import(session: SessionDep) -> CsvImportResponse | None:
    evidence_import = session.exec(select(EvidenceImport).where(EvidenceImport.site_id == "pj-office").order_by(EvidenceImport.id.desc())).first()
    if evidence_import is None:
        return None
    proposals = list(session.exec(select(ProposedDevice).where(ProposedDevice.evidence_import_id == evidence_import.id).order_by(ProposedDevice.row_number)))
    return CsvImportResponse(
        evidence_import=EvidenceImportRead(id=evidence_import.id, filename=evidence_import.filename, source=evidence_import.source, observed_at=evidence_import.observed_at, imported_at=evidence_import.imported_at, row_count=evidence_import.row_count),
        proposals=[ProposedDeviceRead(id=proposal.id, row_number=proposal.row_number, raw_row=proposal.raw_row, name=proposal.name, device_type=proposal.device_type, brand=proposal.brand, model=proposal.model, ip_address=proposal.ip_address, serial_number=proposal.serial_number, source=proposal.source, confidence=proposal.confidence, observed_at=proposal.observed_at, review_status=proposal.review_status) for proposal in proposals],
    )
