"""Standalone live disease-reversal tool (a self-contained ``GET /disease-reversal`` page).

The interactive front for the P0-K reversal engine and the P3-M "bring your own
disease signature" path. A single dependency-free HTML page served by the FastAPI
app that drives the **existing** ``/api/disease_reversal`` endpoints end to end:
pick a builtin signature OR paste up/down gene sets, then rank every perturbation
by how strongly its knockdown reverses that signature.

Why it lives here and not in the static React portal: exactly the same boundary
as ``upload_ui.py`` — the portal is a frozen static build that never calls the
live API, so any live, open-ended query tool belongs on a server-rendered page
that talks only to the same-origin API. Additive: it introduces no new
data-mutating endpoint (it only GET/POSTs endpoints that already exist) and
changes no existing response. Honest-by-design: the reversal payload's
``min_hits`` / ``n_below_min_hits`` and the CRISPRi/context-mismatch caveat are
surfaced verbatim, not hidden.
"""

from __future__ import annotations

from fastapi import APIRouter
from fastapi.responses import HTMLResponse

router = APIRouter(tags=["Disease reversal (research use)"])

_PAGE = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Disease-signature reversal · GWT target tool</title>
<style>
  :root { color-scheme: light dark; --bd:#8886; --accent:#7c3aed; --warn:#b45309; --ok:#15803d; }
  * { box-sizing: border-box; }
  body { font: 15px/1.5 system-ui, sans-serif; margin: 0; padding: 24px; max-width: 960px; }
  h1 { font-size: 1.4rem; margin: 0 0 4px; }
  .sub { opacity: .75; margin: 0 0 16px; }
  .banner { border:1px solid var(--warn); border-radius:8px; padding:10px 12px; margin:0 0 18px; font-size:.9rem; }
  fieldset { border:1px solid var(--bd); border-radius:10px; margin:0 0 16px; padding:14px 16px; }
  legend { padding:0 6px; font-weight:600; }
  label { display:block; margin:8px 0 4px; font-size:.88rem; opacity:.85; }
  input, select, button, textarea { font: inherit; padding:7px 9px; border:1px solid var(--bd); border-radius:7px; background:transparent; color:inherit; width:100%; }
  textarea { min-height:70px; font-family: ui-monospace, monospace; font-size:.85rem; }
  button { cursor:pointer; background:var(--accent); color:#fff; border-color:transparent; width:auto; }
  button.secondary { background:transparent; color:inherit; border-color:var(--bd); }
  button:disabled { cursor:not-allowed; opacity:.5; }
  table { border-collapse:collapse; width:100%; font-size:.86rem; margin-top:8px; }
  th,td { border:1px solid var(--bd); padding:5px 8px; text-align:left; }
  .pill { display:inline-block; padding:1px 8px; border-radius:999px; font-size:.78rem; border:1px solid var(--bd); }
  .pill.rev { color:var(--ok); border-color:var(--ok); }
  .pill.wor { color:var(--warn); border-color:var(--warn); }
  .muted { opacity:.7; font-size:.85rem; }
  .row { display:flex; gap:12px; flex-wrap:wrap; }
  .row > div { flex:1; min-width:220px; }
</style>
</head>
<body>
<h1>Disease-signature reversal <span class="pill">research use</span></h1>
<p class="sub">Which knockdown pushes CD4 T cells <em>away</em> from a disease state? Pick a builtin signature or bring your own up/down gene sets.</p>
<div class="banner">Descriptive hypothesis-generation only. CRISPRi knockdown is not pharmacologic inhibition; a positive reversal score is a hypothesis to test, not a therapeutic claim. Absent measurements are unknown, never zero.</div>

<fieldset>
  <legend>1 · Choose a signature</legend>
  <div class="row">
    <div>
      <label>Builtin signature</label>
      <select id="builtin"><option value="">— none (use my own genes below) —</option></select>
    </div>
    <div>
      <label>Condition</label>
      <select id="cond"><option value="">all</option><option>Rest</option><option>Stim8hr</option><option>Stim48hr</option></select>
    </div>
  </div>
  <label>Disease-UP genes (comma / whitespace separated) — used only if no builtin is picked</label>
  <textarea id="up" placeholder="GATA3, IL4, IL13 ..."></textarea>
  <label>Disease-DOWN genes</label>
  <textarea id="down" placeholder="TBX21, IFNG ..."></textarea>
  <div class="row" style="margin-top:10px">
    <div><label>Min supporting genes (min_hits)</label><input id="minhits" type="number" value="3" min="1"></div>
    <div><label>Top N</label><input id="top" type="number" value="50" min="1"></div>
  </div>
  <div style="margin-top:12px"><button id="run">Rank reversal</button></div>
</fieldset>

<fieldset>
  <legend>2 · Results</legend>
  <p id="meta" class="muted">No query run yet.</p>
  <div id="out"></div>
</fieldset>

<script>
const $ = (id) => document.getElementById(id);
async function api(method, path, body) {
  const opt = { method, headers: {} };
  if (body) { opt.headers['Content-Type'] = 'application/json'; opt.body = JSON.stringify(body); }
  const r = await fetch(path, opt);
  if (!r.ok) { let d=''; try { d=(await r.json()).detail||''; } catch(e){} throw new Error(r.status+' '+d); }
  return r.json();
}
function pill(txt, cls) { return `<span class="pill ${cls||''}">${txt}</span>`; }
function tokens(s) { return (s||'').split(/[^A-Za-z0-9_.-]+/).map(x=>x.trim()).filter(Boolean); }

async function loadSignatures() {
  try {
    const res = await api('GET', '/api/disease_reversal/signatures');
    const sel = $('builtin');
    (res.signatures||[]).forEach(s => {
      const o = document.createElement('option');
      o.value = s.id;
      o.textContent = s.available ? `${s.label} (up ${s.n_up} / down ${s.n_down})` : `${s.label} (unavailable)`;
      sel.appendChild(o);
    });
  } catch (e) { $('meta').textContent = 'Could not load builtin signatures: ' + e.message; }
}

function renderResults(res) {
  $('meta').innerHTML = `signature total ${res.n_signature_total} genes · condition ${res.condition} · `
    + `min_hits ${res.min_hits} (dropped ${res.n_below_min_hits} low-support rows) · ${res.results.length} shown`
    + `<br><span class="muted">${res.caveat||''}</span>`;
  const rows = (res.results||[]).map(r => {
    const cls = r.direction==='reverses_disease' ? 'rev' : (r.direction==='worsens_disease' ? 'wor' : '');
    return `<tr><td><b>${r.target_gene}</b></td><td>${r.culture_condition}</td>`
      + `<td>${r.reversal_score>=0?'+':''}${r.reversal_score.toFixed(3)}</td>`
      + `<td>${pill(r.direction.replace('_disease',''), cls)}</td>`
      + `<td class="muted">${r.n_signature_hit}/${r.n_signature_total} (↑${r.n_up_hit}/↓${r.n_down_hit})</td></tr>`;
  }).join('');
  $('out').innerHTML = rows
    ? `<table><thead><tr><th>target</th><th>condition</th><th>reversal</th><th>direction</th><th>support</th></tr></thead><tbody>${rows}</tbody></table>`
    : `<p class="muted">No rows met the min_hits floor. Lower it, or provide a larger signature.</p>`;
}

$('run').onclick = async () => {
  $('run').disabled = true; $('out').innerHTML=''; $('meta').textContent='Running…';
  try {
    const builtin = $('builtin').value;
    const cond = $('cond').value || null;
    const minhits = parseInt($('minhits').value||'3', 10);
    const top = parseInt($('top').value||'50', 10);
    let res;
    if (builtin) {
      // Builtin path: rank server-side by name so the (large) gene list never
      // travels to the client.
      res = await api('GET', `/api/disease_reversal/_rank_builtin?signature=${encodeURIComponent(builtin)}&condition=${cond||''}&min_hits=${minhits}&top=${top}`);
    } else {
      res = await api('POST', '/api/disease_reversal', { up: tokens($('up').value), down: tokens($('down').value), condition: cond, min_hits: minhits, top });
    }
    renderResults(res);
  } catch (e) { $('meta').textContent = 'Query failed: ' + e.message; }
  finally { $('run').disabled = false; }
};

loadSignatures();
</script>
</body>
</html>
"""


@router.get("/disease-reversal", include_in_schema=False)
def disease_reversal_page() -> HTMLResponse:
    return HTMLResponse(content=_PAGE)
