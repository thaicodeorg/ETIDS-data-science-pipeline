'use client';

import { useEffect, useState } from 'react';

type AnyRecord = Record<string, any>;

const API = process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8000';
const SUPERSET = process.env.NEXT_PUBLIC_SUPERSET_URL || 'http://localhost:8088';
const AIRFLOW = process.env.NEXT_PUBLIC_AIRFLOW_URL || 'http://localhost:8080';

function fmt(value: any) {
  if (value === null || value === undefined) return '—';
  if (typeof value === 'number') {
    if (Math.abs(value) < 1) return value.toFixed(3);
    return value.toLocaleString();
  }
  return String(value);
}

export default function Page() {
  const [busy, setBusy] = useState<string | null>(null);
  const [log, setLog] = useState<any>(null);
  const [kpis, setKpis] = useState<AnyRecord>({});
  const [dq, setDq] = useState<AnyRecord[]>([]);
  const [oee, setOee] = useState<AnyRecord[]>([]);
  const [lines, setLines] = useState<AnyRecord[]>([]);
  const [flow, setFlow] = useState<AnyRecord>({});

  async function call(path: string, method = 'GET') {
    setBusy(path);
    try {
      const res = await fetch(`${API}${path}`, { method });
      if (!res.ok) throw new Error(await res.text());
      const data = await res.json();
      setLog(data);
      return data;
    } finally {
      setBusy(null);
    }
  }

  async function refresh() {
    try {
      const [k, q, o, l, f] = await Promise.all([
        fetch(`${API}/dashboard/kpis`).then(r => r.json()),
        fetch(`${API}/quality/summary`).then(r => r.json()),
        fetch(`${API}/dashboard/oee-daily?limit=20`).then(r => r.json()),
        fetch(`${API}/dashboard/line-performance`).then(r => r.json()),
        fetch(`${API}/pipeline/flow`).then(r => r.json())
      ]);
      setKpis(k || {});
      setDq(q || []);
      setOee(o || []);
      setLines(l || []);
      setFlow(f || {});
    } catch (err: any) {
      setLog({ message: 'Dashboard data is not ready yet. Run the pipeline first.', error: err.message });
    }
  }

  useEffect(() => { refresh(); }, []);

  const kpiCards = [
    ['Work Orders', kpis.work_orders],
    ['Production Runs', kpis.production_runs],
    ['Average OEE', kpis.avg_oee],
    ['High/Medium DQ Issues', kpis.dq_issues_high_medium]
  ];

  return (
    <main>
      <section className="hero">
        <span className="badge">OBE03 · Lectures 3–4</span>
        <h1>Manufacturing Data Science Pipeline</h1>
        <p>
          Control a local Docker-based pipeline: ingest raw manufacturing data, clean and validate it,
          build analytical features, and publish dashboard-ready marts for Superset.
        </p>
      </section>

      <section className="grid">
        {kpiCards.map(([label, value]) => (
          <div className="card" key={label as string}>
            <div className="kpi">{fmt(value)}</div>
            <div className="kpiLabel">{label}</div>
          </div>
        ))}
      </section>

      <section className="card" style={{ marginTop: 18 }}>
        <h2>Pipeline Control</h2>
        <p>
          Lecture 3 uses raw data, Pandas cleaning, validation, and feature engineering. Lecture 4 uses PostgreSQL data marts, Superset datasets, metric layer, charts, dashboards, and RLS policies.
        </p>
        <div className="actions">
          <button disabled={!!busy} onClick={() => call('/pipeline/ingest', 'POST')}>1. Ingest raw data</button>
          <button disabled={!!busy} onClick={() => call('/pipeline/clean', 'POST')}>2. Clean and validate</button>
          <button disabled={!!busy} onClick={() => call('/pipeline/features', 'POST')}>3. Build feature marts</button>
          <button className="secondary" disabled={!!busy} onClick={() => call('/pipeline/run-all', 'POST')}>Run full pipeline</button>
          <button className="warning" disabled={!!busy} onClick={refresh}>Refresh dashboard data</button>
          <a className="linkButton" href={`${API}/docs`} target="_blank">FastAPI docs</a>
          <a className="linkButton" href={AIRFLOW} target="_blank">Open Airflow</a>
          <a className="linkButton" href={SUPERSET} target="_blank">Open Superset</a>
        </div>
        {busy && <p>Running: {busy}</p>}
        {log && <pre>{JSON.stringify(log, null, 2)}</pre>}
      </section>

      <section className="card" style={{ marginTop: 18 }}>
        <h2>Revised Teaching Flow</h2>
        <p>Raw data → ETL / ELT Layer with Python, Pandas, and Airflow → PostgreSQL Data Warehouse / Data Mart → Apache Superset semantic and decision layer.</p>
        <table>
          <thead><tr><th>Layer</th><th>Object / Tool</th></tr></thead>
          <tbody>
            {(flow.flow || []).map((item: string, i: number) => (
              <tr key={i}><td>{i + 1}</td><td>{item}</td></tr>
            ))}
          </tbody>
        </table>
      </section>

      <section className="twoCol">
        <div className="card">
          <h3>Lecture 3: Data Quality Summary</h3>
          <table>
            <thead><tr><th>Severity</th><th>Rule</th><th>Table</th><th>Count</th></tr></thead>
            <tbody>
              {dq.slice(0, 10).map((r, i) => (
                <tr key={i}><td>{fmt(r.severity)}</td><td>{fmt(r.rule_id)}</td><td>{fmt(r.table_name)}</td><td>{fmt(r.issue_count)}</td></tr>
              ))}
            </tbody>
          </table>
        </div>
        <div className="card">
          <h3>Lecture 4: Line Performance</h3>
          <table>
            <thead><tr><th>Plant</th><th>Line</th><th>Avg OEE</th><th>Scrap</th></tr></thead>
            <tbody>
              {lines.slice(0, 10).map((r, i) => (
                <tr key={i}><td>{fmt(r.plant_id)}</td><td>{fmt(r.line_id)}</td><td>{fmt(r.avg_oee)}</td><td>{fmt(r.avg_scrap_rate)}</td></tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>

      <section className="card" style={{ marginTop: 16 }}>
        <h3>Latest OEE Records</h3>
        <table>
          <thead><tr><th>Date</th><th>Plant</th><th>Line</th><th>OEE</th><th>Availability</th><th>Performance</th><th>Quality</th><th>Output</th></tr></thead>
          <tbody>
            {oee.slice(0, 20).map((r, i) => (
              <tr key={i}>
                <td>{fmt(r.production_date)}</td><td>{fmt(r.plant_id)}</td><td>{fmt(r.line_id)}</td>
                <td>{fmt(r.oee)}</td><td>{fmt(r.availability)}</td><td>{fmt(r.performance)}</td><td>{fmt(r.quality)}</td><td>{fmt(r.output_quantity)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </section>
    </main>
  );
}
