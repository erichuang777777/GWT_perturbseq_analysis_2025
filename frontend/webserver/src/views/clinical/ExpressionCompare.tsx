import { useMemo, useRef, useState } from "react";
import type { RealTarget } from "../../data/types";
import { READINESS } from "../../data/reference";
import { parseExpression, compareToReference, type CompareResult } from "../../lib/exprCompare";
import { downloadFile, toCSV } from "../../lib/download";

// Clinical storyline: a clinician pastes or uploads a DE-IDENTIFIED gene-level
// expression-feature table (gene symbol + numeric value; no PII) and we compare
// it, entirely in the browser, against the GWT CD4 Perturb-seq reference target
// set. Nothing is transmitted. This is an overlap lookup framed as hypothesis
// generation, never a diagnostic or a validated signature classifier.

const GREEN = "#0d7d5a";

const EXAMPLE = `gene,value
IL2RA,2.4
CD3E,1.8
VAV1,-2.1
STAT3,1.2
PLCG1,-1.6
FOXP3,0.9
CTLA4,1.4
TNFAIP3,-0.7`;

export default function ExpressionCompare({ targets }: { targets: RealTarget[] }) {
  const [text, setText] = useState("");
  const [result, setResult] = useState<CompareResult | null>(null);
  const [warnings, setWarnings] = useState<string[]>([]);
  const [blocked, setBlocked] = useState<string | null>(null);
  const fileRef = useRef<HTMLInputElement>(null);

  const run = (raw: string) => {
    setResult(null); setBlocked(null); setWarnings([]);
    const parsed = parseExpression(raw);
    if (!parsed.ok) {
      if (parsed.piiColumns.length) setBlocked(parsed.warnings[0]);
      else setWarnings(parsed.warnings);
      return;
    }
    setWarnings(parsed.warnings);
    setResult(compareToReference(parsed.rows, targets));
  };

  const onFile = (f: File) => {
    const reader = new FileReader();
    reader.onload = () => {
      const t = String(reader.result ?? "");
      setText(t.length > 20000 ? t.slice(0, 20000) : t);
      run(t);
    };
    reader.readAsText(f);
  };

  const exportCsv = () => {
    if (!result) return;
    const csv = toCSV(result.matched, [
      ["gene", (m) => m.gene],
      ["patient_value", (m) => (m.patientValue ?? "")],
      ["gwt_readiness_call", (m) => m.call],
      ["gwt_effect", (m) => (m.effect ?? "")],
      ["gwt_median_logFC", (m) => (m.medianLogFC ?? "")],
      ["direction_vs_perturbation", (m) => m.concordance],
      ["module", (m) => (m.module ?? "")],
      ["top_disease", (m) => (m.topDisease ?? "")],
    ]);
    downloadFile(`expression_overlap_${result.nMatched}matched.csv`, csv, "text/csv;charset=utf-8");
  };

  const card: React.CSSProperties = { border: "1px solid #e2e5ea", borderRadius: "14px", padding: "20px 22px", background: "#fff" };
  const callChips = useMemo(() => {
    if (!result) return [];
    return (["advance", "validate", "watchlist", "deprioritize", "unreviewed"] as const)
      .filter((k) => (result.byCall[k] ?? 0) > 0)
      .map((k) => {
        const meta = (READINESS as Record<string, { label: string; color: string; bg: string }>)[k] ?? { label: k, color: "#6b7280", bg: "#f2f3f6" };
        return { k, label: meta.label, color: meta.color, bg: meta.bg, count: result.byCall[k] };
      });
  }, [result]);

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: "18px" }}>
      {/* clinical-use disclaimer */}
      <div style={{ padding: "13px 16px", background: "#fdf6e3", border: "1px solid #eddfc0", borderRadius: "11px", fontSize: "13px", color: "#7a6420", lineHeight: 1.55 }}>
        <strong style={{ color: "#8a6516" }}>Research / hypothesis-generating use only — not clinical software, not a diagnostic.</strong>{" "}
        This compares an anonymised gene-level expression-feature list against the CD4 Perturb-seq reference targets. It never
        recommends a treatment and does not classify a disease. CRISPRi ≠ pharmacology: an in-vitro perturbation signal is a
        research lead, not evidence of efficacy or safety in a patient.
      </div>

      {/* privacy / how-to */}
      <div style={card}>
        <div style={{ fontSize: "16px", fontWeight: 700, marginBottom: "8px" }}>Compare your expression features</div>
        <p style={{ margin: "0 0 12px", fontSize: "13.5px", lineHeight: 1.65, color: "#3a414d" }}>
          Upload or paste a <strong>de-identified</strong> two-column table: a <code style={{ fontFamily: "'IBM Plex Mono', monospace" }}>gene</code> symbol and a
          numeric <code style={{ fontFamily: "'IBM Plex Mono', monospace" }}>value</code> (e.g. a log2 fold-change vs your own control, a z-score, or a
          +1/−1 direction). <strong>No patient identifiers</strong> — the file is checked and refused if it carries name / MRN / DOB / age / sex-type columns.
        </p>
        <div style={{ padding: "10px 13px", background: "#eef7f2", border: "1px solid #cfe8dd", borderRadius: "9px", fontSize: "12.5px", color: "#2f6f56", lineHeight: 1.5, marginBottom: "14px" }}>
          🔒 <strong>Your data never leaves this page.</strong> The comparison runs entirely in your browser — nothing is uploaded to any server, stored, or logged.
        </div>

        <div style={{ display: "flex", gap: "10px", flexWrap: "wrap", alignItems: "center", marginBottom: "12px" }}>
          <input
            ref={fileRef}
            type="file"
            accept=".csv,.tsv,.txt"
            onChange={(e) => { const f = e.target.files?.[0]; if (f) onFile(f); }}
            style={{ fontSize: "13px" }}
          />
          <button
            onClick={() => { setText(EXAMPLE); run(EXAMPLE); }}
            style={{ padding: "8px 14px", border: "1.5px solid #d6dbe3", borderRadius: "9px", background: "#fff", color: "#4a515e", fontSize: "12.5px", fontWeight: 600, cursor: "pointer" }}
          >
            Load example
          </button>
        </div>

        <textarea
          value={text}
          onChange={(e) => setText(e.target.value)}
          placeholder={"Paste here, e.g.\ngene,value\nIL2RA,2.4\nCD3E,1.8\nVAV1,-2.1"}
          rows={7}
          style={{ width: "100%", boxSizing: "border-box", fontFamily: "'IBM Plex Mono', monospace", fontSize: "12.5px", padding: "11px 13px", border: "1px solid #d6dbe3", borderRadius: "10px", resize: "vertical", lineHeight: 1.5 }}
        />
        <div style={{ display: "flex", gap: "10px", marginTop: "12px" }}>
          <button
            onClick={() => run(text)}
            disabled={!text.trim()}
            style={{ padding: "9px 20px", border: "none", borderRadius: "9px", background: text.trim() ? GREEN : "#c5ccd6", color: "#fff", fontSize: "13px", fontWeight: 600, cursor: text.trim() ? "pointer" : "not-allowed" }}
          >
            Compare against reference
          </button>
          {(text || result || blocked) && (
            <button
              onClick={() => { setText(""); setResult(null); setBlocked(null); setWarnings([]); if (fileRef.current) fileRef.current.value = ""; }}
              style={{ padding: "9px 16px", border: "1.5px solid #d6dbe3", borderRadius: "9px", background: "#fff", color: "#4a515e", fontSize: "13px", fontWeight: 500, cursor: "pointer" }}
            >
              Clear
            </button>
          )}
        </div>
      </div>

      {/* PII block */}
      {blocked && (
        <div style={{ ...card, borderColor: "#e6b8b8", background: "#fcf3f3" }}>
          <div style={{ fontSize: "14px", fontWeight: 700, color: "#b23b3b", marginBottom: "5px" }}>Upload refused — identifiers detected</div>
          <p style={{ margin: 0, fontSize: "13px", color: "#8a4b4b", lineHeight: 1.6 }}>{blocked}</p>
        </div>
      )}

      {/* warnings */}
      {warnings.length > 0 && (
        <div style={{ fontSize: "12.5px", color: "#7a6a3f", background: "#fbf9f2", border: "1px solid #eddfc0", borderRadius: "9px", padding: "11px 14px", lineHeight: 1.5 }}>
          {warnings.map((w, i) => <div key={i}>• {w}</div>)}
        </div>
      )}

      {/* results */}
      {result && (
        <>
          <div style={card}>
            <div style={{ display: "flex", alignItems: "baseline", justifyContent: "space-between", flexWrap: "wrap", gap: "10px", marginBottom: "14px" }}>
              <div style={{ fontSize: "16px", fontWeight: 700 }}>
                {result.nMatched} of {result.nUploaded} genes are reference perturbation targets
              </div>
              {result.nMatched > 0 && (
                <button onClick={exportCsv} style={{ padding: "7px 14px", border: "1.5px solid #d6dbe3", borderRadius: "8px", background: "#fff", color: "#1a5fb4", fontSize: "12.5px", fontWeight: 600, cursor: "pointer" }}>
                  Export overlap CSV
                </button>
              )}
            </div>

            {result.nMatched === 0 ? (
              <p style={{ margin: 0, fontSize: "13px", color: "#6b7280", lineHeight: 1.6 }}>
                None of the uploaded genes are among the {targets.length.toLocaleString()} screened targets in this reference set.
                That is a real, honest result — the screen covers a defined gene set, and non-overlap simply means these features fall outside it.
              </p>
            ) : (
              <>
                {/* readiness distribution of the overlap */}
                <div style={{ fontSize: "12px", fontWeight: 700, letterSpacing: ".4px", color: "#8a92a0", textTransform: "uppercase", marginBottom: "8px" }}>Reference readiness call of matched genes</div>
                <div style={{ display: "flex", flexWrap: "wrap", gap: "8px", marginBottom: "8px" }}>
                  {callChips.map((c) => (
                    <span key={c.k} style={{ display: "inline-flex", alignItems: "center", gap: "7px", padding: "6px 12px", borderRadius: "8px", background: c.bg, color: c.color, fontSize: "12.5px", fontWeight: 600 }}>
                      {c.label}<span style={{ fontWeight: 700 }}>{c.count}</span>
                    </span>
                  ))}
                </div>
                <p style={{ margin: 0, fontSize: "12px", color: "#9aa1ad", lineHeight: 1.5 }}>
                  The readiness call is the reference screen's own four-level triage (advance / validate / watchlist / deprioritize) — it describes the CD4 perturbation evidence for that gene, not your sample.
                </p>
              </>
            )}
          </div>

          {/* module + disease context */}
          {result.nMatched > 0 && (result.moduleCounts.length > 0 || result.diseaseCounts.length > 0) && (
            <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "16px" }}>
              {result.moduleCounts.length > 0 && (
                <div style={card}>
                  <div style={{ fontSize: "14px", fontWeight: 700, marginBottom: "10px" }}>Immune-concept modules</div>
                  {result.moduleCounts.slice(0, 8).map((m) => (
                    <div key={m.module} style={{ display: "flex", justifyContent: "space-between", fontSize: "12.5px", padding: "4px 0", color: "#3a414d" }}>
                      <span style={{ fontFamily: "'IBM Plex Mono', monospace", color: "#1a5fb4" }}>{m.module}</span>
                      <span style={{ fontWeight: 600 }}>{m.count}</span>
                    </div>
                  ))}
                </div>
              )}
              {result.diseaseCounts.length > 0 && (
                <div style={card}>
                  <div style={{ fontSize: "14px", fontWeight: 700, marginBottom: "10px" }}>Top disease links (Open Targets)</div>
                  {result.diseaseCounts.slice(0, 8).map((d) => (
                    <div key={d.id} style={{ display: "flex", justifyContent: "space-between", gap: "10px", fontSize: "12.5px", padding: "4px 0", color: "#3a414d" }}>
                      <span style={{ minWidth: 0, overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>{d.name}</span>
                      <span style={{ fontWeight: 600 }}>{d.count}</span>
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}

          {/* matched gene table */}
          {result.nMatched > 0 && (
            <div style={card}>
              <div style={{ fontSize: "14px", fontWeight: 700, marginBottom: "12px" }}>Matched genes</div>
              <div style={{ overflowX: "auto" }}>
                <table style={{ width: "100%", borderCollapse: "collapse", fontSize: "12.5px" }}>
                  <thead>
                    <tr style={{ textAlign: "left", color: "#8a92a0", fontSize: "11px", textTransform: "uppercase", letterSpacing: ".4px" }}>
                      <th style={{ padding: "6px 8px" }}>Gene</th>
                      <th style={{ padding: "6px 8px" }}>Your value</th>
                      <th style={{ padding: "6px 8px" }}>Reference call</th>
                      <th style={{ padding: "6px 8px" }}>Effect</th>
                      <th style={{ padding: "6px 8px" }}>Direction</th>
                      <th style={{ padding: "6px 8px" }}>Top disease</th>
                    </tr>
                  </thead>
                  <tbody>
                    {result.matched.map((m) => {
                      const meta = (READINESS as Record<string, { label: string; color: string; bg: string }>)[m.call] ?? { label: m.call, color: "#6b7280", bg: "#f2f3f6" };
                      return (
                        <tr key={m.gene} style={{ borderTop: "1px solid #eef0f3" }}>
                          <td style={{ padding: "7px 8px", fontWeight: 600, fontFamily: "'IBM Plex Mono', monospace", color: "#1a1d24" }}>{m.gene}</td>
                          <td style={{ padding: "7px 8px", color: "#4a515e", fontFamily: "'IBM Plex Mono', monospace" }}>{m.patientValue != null ? m.patientValue : "—"}</td>
                          <td style={{ padding: "7px 8px" }}>
                            <span style={{ padding: "2px 9px", borderRadius: "6px", background: meta.bg, color: meta.color, fontWeight: 600, fontSize: "11.5px" }}>{meta.label}</span>
                          </td>
                          <td style={{ padding: "7px 8px", color: "#4a515e", fontFamily: "'IBM Plex Mono', monospace" }}>{m.effect != null ? m.effect.toFixed(2) : "—"}</td>
                          <td style={{ padding: "7px 8px", color: m.concordance === "concordant" ? GREEN : m.concordance === "opposing" ? "#b23b3b" : "#9aa1ad" }}>{m.concordance}</td>
                          <td style={{ padding: "7px 8px", color: "#4a515e", maxWidth: "180px", overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>{m.topDisease ?? "—"}</td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>
              <p style={{ margin: "12px 0 0", fontSize: "11.5px", color: "#9aa1ad", lineHeight: 1.5 }}>
                <strong>Direction</strong> compares the sign of your value against the sign of the perturbation's median downstream logFC — a coarse
                same/opposite flag, not a statistical concordance test. Genes with no numeric value or no reference logFC show <em>n/a</em>.
              </p>
            </div>
          )}
        </>
      )}
    </div>
  );
}
