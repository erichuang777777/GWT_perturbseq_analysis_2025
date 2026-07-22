"""Standalone live upload tool (a self-contained ``GET /upload`` page).

This is the "approach C" upload UI: a single, dependency-free HTML page served
by the FastAPI app that drives the **existing** ``/api/imports/*`` staging flow
end to end — upload → column mapping → approve → merge → **real readiness** — and
shows the actual `compute_readiness` output for the newly built dataset.

Why it lives here and not in the React portal:

- The React portal (`frontend/webserver/`) is a **static** build baked from a
  one-time `export_real_data.py` run; it does not call the live backend at
  runtime, and it is intentionally frozen for release. Wiring a live,
  state-mutating upload flow into it would un-freeze it.
- This page instead talks only to the live API on the same origin, so it works
  wherever the API runs (`make api` → http://127.0.0.1:8000/upload) without any
  build step, npm, or bundler — the same "independently deployable, HTTP/JSON
  only" boundary the rest of the frontend respects.

It is additive: it introduces no new endpoint that mutates data (every action
POSTs to an endpoint that already exists) and changes no existing response.
Honest-by-design: the staging/review states (`staged_exploratory_review_required`,
`staged_low_context_review_required`, schema-blocked) are surfaced verbatim rather
than hidden, and the readiness panel reproduces the `unknown != 0` disclosure
(overlays_used vs overlays_missing) instead of implying full coverage.
"""

from __future__ import annotations

from fastapi import APIRouter
from fastapi.responses import HTMLResponse

router = APIRouter(tags=["Uploads"])

_PAGE = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Upload a screen · GWT target tool</title>
<style>
  :root { color-scheme: light dark; --bd:#8886; --accent:#2563eb; --warn:#b45309; --ok:#15803d; }
  * { box-sizing: border-box; }
  body { font: 15px/1.5 system-ui, sans-serif; margin: 0; padding: 24px; max-width: 900px; }
  h1 { font-size: 1.4rem; margin: 0 0 4px; }
  .sub { opacity: .75; margin: 0 0 16px; }
  .banner { border:1px solid var(--warn); border-radius:8px; padding:10px 12px; margin:0 0 18px; font-size:.9rem; }
  fieldset { border:1px solid var(--bd); border-radius:10px; margin:0 0 16px; padding:14px 16px; }
  fieldset[disabled] { opacity:.5; }
  legend { padding:0 6px; font-weight:600; }
  label { display:block; margin:8px 0 4px; font-size:.88rem; opacity:.85; }
  input, select, button { font: inherit; padding:7px 9px; border:1px solid var(--bd); border-radius:7px; background:transparent; color:inherit; }
  button { cursor:pointer; background:var(--accent); color:#fff; border-color:transparent; }
  button.secondary { background:transparent; color:inherit; border-color:var(--bd); }
  button:disabled { cursor:not-allowed; opacity:.5; }
  table { border-collapse:collapse; width:100%; font-size:.86rem; margin-top:8px; }
  th,td { border:1px solid var(--bd); padding:5px 8px; text-align:left; }
  .pill { display:inline-block; padding:1px 8px; border-radius:999px; font-size:.78rem; border:1px solid var(--bd); }
  .pill.ok { color:var(--ok); border-color:var(--ok); }
  .pill.warn { color:var(--warn); border-color:var(--warn); }
  .muted { opacity:.7; }
  pre { background:#8881; padding:10px; border-radius:8px; overflow:auto; font-size:.82rem; }
  .row { display:flex; gap:10px; flex-wrap:wrap; align-items:end; }
  .hidden { display:none; }
  code { background:#8882; padding:1px 4px; border-radius:4px; }
</style>
</head>
<body>
<h1>Upload a screen &rarr; live target cards</h1>
<p class="sub">Stages your CSV through the real pipeline (map columns &rarr; approve &rarr; merge) and shows the
actual readiness call &mdash; the same engine that scores the reference dataset.</p>

<div class="banner">🔬 <b>Research / hypothesis-generating use only — not clinical software.</b>
Nothing is persisted beyond this server's local cache. <code>unknown</code> is shown as unknown, never as <code>0</code>.</div>

<fieldset id="fs-upload">
  <legend>1 · Upload</legend>
  <div class="row">
    <div>
      <label for="f">CSV file (target-level DE table)</label>
      <input type="file" id="f" accept=".csv,.tsv,.txt">
    </div>
    <div>
      <label for="name">Source name</label>
      <input type="text" id="name" placeholder="e.g. CD4 T-cell Perturb-seq (my lab)" size="34">
    </div>
    <div>
      <label for="mode">Mode</label>
      <select id="mode">
        <option value="strict">strict (approvable when clean)</option>
        <option value="exploratory">exploratory (review required before merge)</option>
      </select>
    </div>
    <button id="btnUpload">Upload &amp; stage</button>
  </div>
  <p class="muted" style="font-size:.82rem;margin-bottom:0">Tip: strict mode only becomes <code>staged</code> (approvable) when the
  data reads as CD4 / T-cell / immune context and the schema is clean. Anything else stays in a review-required state — shown honestly below.</p>
</fieldset>

<fieldset id="fs-map" disabled>
  <legend>2 · Map columns</legend>
  <p class="muted" id="mapNote"></p>
  <div id="qcPanel"></div>
  <table id="mapTable" class="hidden"><thead><tr><th>canonical field</th><th>your column</th></tr></thead><tbody></tbody></table>
  <div class="row" style="margin-top:10px"><button id="btnMap" class="secondary">Apply mapping</button></div>
</fieldset>

<fieldset id="fs-merge" disabled>
  <legend>3 · Approve &amp; merge</legend>
  <p id="statusLine"></p>
  <div class="row"><button id="btnMerge">Approve &amp; merge to cards</button></div>
</fieldset>

<fieldset id="fs-result" class="hidden">
  <legend>4 · Result &mdash; real readiness</legend>
  <div id="result"></div>
</fieldset>

<script>
const $ = (id) => document.getElementById(id);
let importId = null, suggestion = null, uploadedCols = [], canonicalFields = null;

function pill(txt, cls) { return `<span class="pill ${cls||''}">${txt}</span>`; }

// Pre-flight QC gate (plan P2-A): show cell/guide/DE/donor coverage + missingness
// BEFORE approve, and cap the merge button on a hard block. unknown != 0 —
// absent gate columns render as "unknown", never a silent pass.
function renderQC(qc) {
  const el = $('qcPanel');
  if (!qc) { el.innerHTML = ''; return; }
  const gateCls = qc.gate === 'block' ? 'warn' : (qc.gate === 'warn' ? 'warn' : 'ok');
  const rows = (qc.checks || []).map(c => {
    const cls = c.status === 'block' ? 'warn' : (c.status === 'warn' ? 'warn' : (c.status === 'unknown' ? '' : 'ok'));
    let detail = c.detail || '';
    if (c.present && c.median != null && detail === '') {
      detail = `median ${c.median}` + (c.floor != null ? ` (floor ${c.floor})` : '')
             + (c.n_below_floor ? ` · ${c.n_below_floor} below floor` : '')
             + (c.n_donors != null ? `` : '');
    }
    if (c.n_donors != null && detail === '') detail = `${c.n_donors} donor(s)`;
    return `<tr><td>${c.label}</td><td>${pill(c.status, cls)}</td><td class="muted">${detail}</td></tr>`;
  }).join('');
  el.innerHTML = `<div class="card" style="margin:8px 0">`
    + `<b>Pre-flight QC</b> ${pill(qc.gate, gateCls)} <span class="muted">· ${qc.sampled_rows} preview rows · floors: ${qc.thresholds.min_cells} cells / ${qc.thresholds.min_de_genes} DE genes</span>`
    + `<table style="margin-top:6px"><tbody>${rows}</tbody></table>`
    + (qc.gate === 'block' ? `<p class="muted" style="color:#b4402a">A gate's median is below the floor — this dataset would be capped at merge. Review before approving.</p>` : '')
    + `<p class="muted">${qc.note}</p></div>`;
}
function setEnabled(fs, on) { $(fs).disabled = !on; }

async function api(method, path, body) {
  const opt = { method, headers: {} };
  if (body !== undefined) { opt.headers['Content-Type'] = 'application/json'; opt.body = JSON.stringify(body); }
  const r = await fetch(path, opt);
  const txt = await r.text();
  let data; try { data = JSON.parse(txt); } catch { data = txt; }
  if (!r.ok) throw new Error((data && data.detail) ? data.detail : ('HTTP ' + r.status));
  return data;
}

function readFileB64(file) {
  return new Promise((res, rej) => {
    const fr = new FileReader();
    fr.onload = () => res(fr.result.split(',')[1]);
    fr.onerror = rej;
    fr.readAsDataURL(file);
  });
}

$('btnUpload').onclick = async () => {
  try {
    const file = $('f').files[0];
    if (!file) { alert('Choose a CSV file first.'); return; }
    $('btnUpload').disabled = true;
    const b64 = await readFileB64(file);
    const res = await api('POST', '/api/imports', {
      source_name: $('name').value || file.name,
      filename: file.name,
      content_base64: b64,
      declared_source_type: 'target_evidence',
      mode: $('mode').value,
    });
    importId = res.import_id;
    uploadedCols = res.columns || [];
    const sug = await api('GET', `/api/imports/${importId}/mapping/suggestion`);
    suggestion = sug.suggested || {};
    canonicalFields = sug.canonical_fields || {};
    renderMapping(sug);
    setEnabled('fs-map', true);
    $('mapNote').innerHTML = `Detected <b>${uploadedCols.length}</b> columns · source type <code>${sug.source_type}</code> · status ${pill(res.merge_status, res.merge_status==='staged'?'ok':'warn')}`;
    renderQC(res.qc_report);
  } catch (e) { alert('Upload failed: ' + e.message); }
  finally { $('btnUpload').disabled = false; }
};

function renderMapping(sug) {
  const req = (canonicalFields.required || []);
  const rec = (canonicalFields.recommended || []);
  const fields = [...req, ...rec];
  const tb = $('mapTable').querySelector('tbody'); tb.innerHTML = '';
  fields.forEach(f => {
    const tr = document.createElement('tr');
    const opts = ['<option value="">— none —</option>']
      .concat(uploadedCols.map(c => `<option ${suggestion[f]===c?'selected':''}>${c}</option>`)).join('');
    tr.innerHTML = `<td><code>${f}</code>${req.includes(f)?' <span class="muted">(required)</span>':''}</td>`
                 + `<td><select data-field="${f}">${opts}</select></td>`;
    tb.appendChild(tr);
  });
  $('mapTable').classList.remove('hidden');
}

$('btnMap').onclick = async () => {
  try {
    const map = {};
    $('mapTable').querySelectorAll('select').forEach(s => { if (s.value) map[s.dataset.field] = s.value; });
    const res = await api('POST', `/api/imports/${importId}/mapping`, { map });
    const st = res.merge_status;
    $('statusLine').innerHTML = `Mapping applied · status ${pill(st, st==='staged'?'ok':'warn')} `
      + (st==='staged' ? '<span class="muted">— clean, ready to approve & merge.</span>'
                       : '<span class="muted">— this state needs review before it can merge (shown honestly; not hidden).</span>');
    setEnabled('fs-merge', true);
    $('btnMerge').disabled = (st !== 'staged');
  } catch (e) { alert('Mapping failed: ' + e.message); }
};

$('btnMerge').onclick = async () => {
  try {
    $('btnMerge').disabled = true;
    await api('POST', `/api/imports/${importId}/approve`, { approved_by: 'upload_ui' });
    const merged = await api('POST', `/api/imports/${importId}/merge`, {});
    const ds = merged.dataset_id;
    const rd = await api('GET', `/api/readiness/${ds}`);
    renderResult(ds, merged, rd);
  } catch (e) { alert('Merge failed: ' + e.message); $('btnMerge').disabled = false; }
};

function renderResult(ds, merged, rd) {
  $('fs-result').classList.remove('hidden');
  const calls = rd.call_counts || {};
  const callRows = Object.keys(calls).sort().map(k => `<tr><td>${k}</td><td>${calls[k]}</td></tr>`).join('') || '<tr><td colspan=2 class=muted>none</td></tr>';
  const used = (rd.overlays_used || []).map(x => pill(x,'ok')).join(' ') || '<span class="muted">none</span>';
  const missing = (rd.overlays_missing || []).map(x => pill(x,'warn')).join(' ') || '<span class="muted">none</span>';
  $('result').innerHTML = `
    <p>Built dataset <code>${ds}</code> · <b>${merged.rows}</b> target rows.</p>
    <p style="margin-bottom:4px"><b>Readiness call counts</b> (real <code>compute_readiness</code> output):</p>
    <table><thead><tr><th>call</th><th>n</th></tr></thead><tbody>${callRows}</tbody></table>
    <p style="margin:12px 0 4px"><b>Overlays used</b>: ${used}</p>
    <p style="margin:0 0 4px"><b>Overlays missing</b> (stay <code>unknown</code>, never <code>0</code>): ${missing}</p>
    <p class="muted" style="font-size:.82rem">Descriptive overlays are kept separate from the readiness call. This is a
    guide-less upload, so on-target knockdown is <code>not_assessed</code> (genuinely unknown) and grade is capped — by design.</p>
    <p><a href="/api/readiness/${ds}" target="_blank">Open full readiness JSON &rarr;</a> ·
       <a href="/api/targets/${ds}" target="_blank">target cards JSON &rarr;</a></p>`;
}
</script>
</body>
</html>"""


@router.get("/upload", response_class=HTMLResponse, include_in_schema=False)
def upload_page() -> str:
    """Serve the standalone live-upload page (drives the /api/imports/* flow)."""
    return _PAGE
