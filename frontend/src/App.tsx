import { useState } from 'react';

type Report = {
  name: string;
  step_file: string;
  solid_count: number;
  solid_valid: boolean;
  dimensions: Record<string, number>;
  dimension_checks: Record<string, { expected_mm: number; measured_mm: number; pass: boolean }>;
  step_reimport_ok: boolean;
  review_flags: string[];
};

export default function App() {
  const [length, setLength] = useState(80);
  const [width, setWidth] = useState(40);
  const [thickness, setThickness] = useState(8);
  const [holeDiameter, setHoleDiameter] = useState(6);
  const [busy, setBusy] = useState(false);
  const [report, setReport] = useState<Report | null>(null);
  const [error, setError] = useState('');

  async function buildDemo() {
    setBusy(true);
    setError('');
    setReport(null);
    try {
      const response = await fetch('http://127.0.0.1:8000/api/build', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          name: 'demo_plate',
          length_mm: length,
          width_mm: width,
          thickness_mm: thickness,
          holes: [
            { x_mm: -length / 4, y_mm: 0, diameter_mm: holeDiameter },
            { x_mm: length / 4, y_mm: 0, diameter_mm: holeDiameter }
          ]
        })
      });
      const data = await response.json();
      if (!response.ok) throw new Error(data.detail ?? 'Build failed');
      setReport(data);
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Could not connect to backend');
    } finally {
      setBusy(false);
    }
  }

  return (
    <main className="shell">
      <header>
        <div className="brand">DRAWING<span>2</span>CAD</div>
        <div className="tag">LOCAL AI ENGINEERING WORKBENCH</div>
      </header>
      <section className="hero">
        <p className="eyebrow">BLACKFORESTHACKATHON · BCT TECHNOLOGY AG</p>
        <h1>From technical drawing<br /><span>to validated 3D CAD.</span></h1>
        <p className="sub">Build the deterministic CAD pipeline first. Then connect drawing recognition and the local AI agent.</p>
      </section>
      <section className="layout">
        <article className="panel">
          <div className="panelTitle"><span>01 / TEST GEOMETRY</span><span className="pill">DEMO MODE</span></div>
          <p className="muted">Generate a test plate to verify CAD construction, validation and STEP export before adding drawing interpretation.</p>
          <label>Length <b>{length} mm</b><input type="range" min="30" max="160" value={length} onChange={e => setLength(+e.target.value)} /></label>
          <label>Width <b>{width} mm</b><input type="range" min="20" max="100" value={width} onChange={e => setWidth(+e.target.value)} /></label>
          <label>Thickness <b>{thickness} mm</b><input type="range" min="3" max="25" value={thickness} onChange={e => setThickness(+e.target.value)} /></label>
          <label>Hole diameter <b>{holeDiameter} mm</b><input type="range" min="2" max="12" value={holeDiameter} onChange={e => setHoleDiameter(+e.target.value)} /></label>
          <button onClick={buildDemo} disabled={busy}>{busy ? 'Building model…' : 'Build & validate STEP'} <span>↗</span></button>
          {error && <p className="error">{error}</p>}
        </article>
        <article className="panel results">
          <div className="panelTitle"><span>02 / VALIDATION REPORT</span><span className="pill">LIVE</span></div>
          {!report && !error && <div className="empty"><div className="cube">◇</div><h2>Awaiting first build</h2><p>Run the demo build to see solid validity, dimension checks and STEP re-import status.</p></div>}
          {report && <>
            <div className="status"><span className="check">✓</span><div><b>{report.solid_valid && report.step_reimport_ok ? 'Validation passed' : 'Review required'}</b><p>Part: {report.name}</p></div></div>
            <div className="metrics"><div><small>SOLIDS</small><strong>{report.solid_count}</strong></div><div><small>STEP RE-IMPORT</small><strong>{report.step_reimport_ok ? 'PASS' : 'FAIL'}</strong></div></div>
            <h3>Dimension comparison</h3>
            {Object.entries(report.dimension_checks).map(([key, check]) => <div className="checkRow" key={key}><span>{key.replace('_mm', '').toUpperCase()}</span><span>{check.measured_mm} mm</span><b className={check.pass ? 'good' : 'bad'}>{check.pass ? 'PASS' : 'FAIL'}</b></div>)}
            <a className="download" href={`http://127.0.0.1:8000/api/files/${report.name}.step`}>Download STEP file ↓</a>
            {report.review_flags.length > 0 && <p className="error">Review: {report.review_flags.join(', ')}</p>}
          </>}
        </article>
      </section>
      <footer><span>DRAWING2CAD / PROTOTYPE 0.1</span><span>LOCAL-FIRST · API-INDEPENDENT</span></footer>
    </main>
  );
}
