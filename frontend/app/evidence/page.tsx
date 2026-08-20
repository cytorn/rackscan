"use client";

import Link from "next/link";
import { ChangeEvent, useEffect, useMemo, useState } from "react";

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://127.0.0.1:8000";
type ReviewItem = { id: number; kind: "field_observation" | "field_conflict"; device_name: string; field_name: string | null; observed_value: string | null; accepted_value: string | null; source: string; confidence: number; observed_at: string; status: string };

export default function EvidencePage() {
  const [queue, setQueue] = useState<ReviewItem[] | null>(null);
  const [mode, setMode] = useState<"csv" | "cli">("csv");
  const [cliText, setCliText] = useState("");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState<number | "import" | null>(null);

  async function loadQueue() {
    setError("");
    try {
      const response = await fetch(`${API_URL}/api/sites/pj-office/review-queue`);
      if (!response.ok) throw new Error("The local API could not load the review queue.");
      setQueue(await response.json());
    } catch (cause) { setError(cause instanceof Error ? cause.message : "The review queue could not be loaded."); }
  }
  useEffect(() => { const request = window.setTimeout(() => void loadQueue(), 0); return () => window.clearTimeout(request); }, []);

  async function submit(url: string, body: object, target: number | "import") {
    setBusy(target); setError("");
    try {
      const response = await fetch(`${API_URL}${url}`, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(body) });
      const data = await response.json();
      if (!response.ok) throw new Error(data.detail ?? "RackScan could not process that evidence.");
      await loadQueue();
    } catch (cause) { setError(cause instanceof Error ? cause.message : "RackScan could not process that evidence."); }
    finally { setBusy(null); }
  }
  async function chooseFile(event: ChangeEvent<HTMLInputElement>) {
    const file = event.target.files?.[0];
    if (!file) return;
    if (!file.name.toLowerCase().endsWith(".csv")) { setError("Choose a .csv inventory file."); return; }
    await submit("/api/sites/pj-office/evidence/csv", { filename: file.name, csv_text: await file.text() }, "import");
    event.target.value = "";
  }
  async function importCli() {
    if (!cliText.trim()) { setError("Paste the ArubaOS-Switch show system output first."); return; }
    await submit("/api/sites/pj-office/evidence/cli", { filename: "aruba-show-system.txt", platform: "arubaos-switch", command: "show system", cli_text: cliText }, "import");
    setCliText("");
  }
  const counts = useMemo(() => ({ conflicts: queue?.filter(item => item.kind === "field_conflict").length ?? 0, pending: queue?.filter(item => item.kind === "field_observation").length ?? 0 }), [queue]);

  return <main className="evidence-page"><header className="evidence-header"><Link href="/">← Back to site overview</Link><div><span className="eyebrow">PHASE 2.5 / EVIDENCE REVIEW</span><h1>Resolve site evidence, field by field</h1><p>RackScan keeps every observation. Accepted device data changes only after an explicit decision.</p></div></header>
    <section className="evidence-intake"><div><span className="eyebrow">EVIDENCE INPUT</span><h2>Add site-survey evidence</h2><p>CSV requires <code>name</code>; CLI supports ArubaOS-Switch <code>show system</code>. Imports create reviewable observations and never overwrite accepted facts.</p><div className="intake-tabs"><button className={mode === "csv" ? "active" : ""} onClick={() => setMode("csv")}>CSV inventory</button><button className={mode === "cli" ? "active" : ""} onClick={() => setMode("cli")}>CLI text</button></div></div>{mode === "csv" ? <label className="file-picker"><input type="file" accept=".csv,text/csv" onChange={chooseFile} disabled={busy !== null} /><span>{busy === "import" ? "Reading evidence…" : "Choose CSV file"}</span><small>Local file · no device connection</small></label> : <div className="cli-input"><textarea aria-label="ArubaOS-Switch show system output" value={cliText} onChange={event => setCliText(event.target.value)} placeholder={"System Name : ACCESS-SW03\nSystem Description : Aruba 2930F 24G PoEP\nSerial Number : CN123456\nIP Address : 10.10.10.5"} /><button className="primary" disabled={busy !== null} onClick={() => void importCli()}>{busy === "import" ? "Parsing…" : "Parse show system"}</button></div>}</section>
    {error && <div className="import-error" role="alert"><strong>Evidence action needs attention.</strong> {error} <button onClick={() => void loadQueue()}>Retry queue</button></div>}
    <section className="review-queue" aria-labelledby="review-queue-title"><div className="proposal-heading"><div><span className="eyebrow">SITE-WIDE REVIEW QUEUE</span><h2 id="review-queue-title">{queue === null ? "Loading review items…" : queue.length ? "Unresolved observations" : "No evidence needs a decision"}</h2><p>{queue === null ? "Retrieving evidence across all imports." : queue.length ? "Inspect the accepted value, observed value, source, confidence, and timestamp before you decide." : "All currently imported observations are accepted, resolved, or rejected."}</p></div>{queue && <div className="proposal-totals"><span><b>{counts.pending}</b> pending</span><span className="conflict-total"><b>{counts.conflicts}</b> conflict</span></div>}</div>
      {queue && queue.length > 0 && <div className="review-list">{queue.map(item => <article className={`review-item-card ${item.kind === "field_conflict" ? "conflict" : ""}`} key={item.id}><div className="review-item-heading"><div><span className="status-label">{item.kind === "field_conflict" ? "CONFLICT" : "OBSERVED CHANGE"}</span><h3>{item.device_name} <small>· {label(item.field_name)}</small></h3></div><strong>{item.confidence}%<small>confidence</small></strong></div><dl><div><dt>Current accepted value</dt><dd className={item.accepted_value ? "" : "unknown"}>{item.accepted_value ?? "Unknown"}</dd></div><div><dt>Observed value</dt><dd>{item.observed_value ?? "Unknown"}</dd></div><div><dt>Evidence</dt><dd>{item.source}</dd></div><div><dt>Observed</dt><dd>{item.observed_at}</dd></div></dl><p className="decision-consequence">{item.kind === "field_conflict" ? "Resolving with the observed value will change the accepted device field; rejecting preserves the current value." : "Accepting adds this observed value to the resolved device record. Rejecting keeps the evidence trace without changing the device."}</p><div className="proposal-actions">{item.kind === "field_conflict" ? <button className="primary" disabled={busy !== null} onClick={() => void submit(`/api/sites/pj-office/observations/${item.id}/resolve`, {}, item.id)}>{busy === item.id ? "Resolving…" : "Resolve with observed value"}</button> : <button className="primary" disabled={busy !== null} onClick={() => void submit(`/api/sites/pj-office/observations/${item.id}/accept`, {}, item.id)}>{busy === item.id ? "Accepting…" : "Accept observation"}</button>}<button disabled={busy !== null} onClick={() => void submit(`/api/sites/pj-office/observations/${item.id}/reject`, {}, item.id)}>Reject observation</button></div></article>)}</div>}
      {queue?.length === 0 && <div className="evidence-empty"><span>✓</span><h2>Review queue clear</h2><p>Bring in another CSV or supported CLI capture when new site-survey evidence arrives.</p></div>}</section>
  </main>;
}

function label(field: string | null) { return field ? field.replaceAll("_", " ") : "device"; }
