import type { RealTarget } from "../../data/types";
import SectionCard, { UnknownNotice } from "../../components/ui/SectionCard";

// Stage-3 "External corroboration" panel: three orthogonal, independent
// external sources re-checked per target (Open Targets GWAS genetics · STRING
// known-partner recovery · GEO GSE318876 CRISPRa HIV screen). Each track is
// shown honestly — a real value with a source link when present, an explicit
// "no external hit" state when the gene is absent from that track. Distinct
// from the Open Targets disease-association score in the scoring weights: this
// is *independent revalidation*, not the same associations re-used.
const OT = "https://platform.opentargets.org/target/";
const STRING_URL = "https://string-db.org/cgi/network?identifiers=";
const GEO_URL = "https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE318876";

function Track({
  label,
  present,
  children,
  href,
  hrefLabel,
  absentNote,
}: {
  label: string;
  present: boolean;
  children?: React.ReactNode;
  href?: string;
  hrefLabel?: string;
  absentNote: string;
}) {
  return (
    <div style={{ border: "1px solid #eef0f3", borderRadius: "11px", padding: "13px 15px", background: present ? "#fff" : "#fafbfc" }}>
      <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", gap: "10px", marginBottom: present ? "9px" : "5px" }}>
        <span style={{ fontSize: "12px", fontWeight: 700, letterSpacing: ".3px", color: "#3a414d" }}>{label}</span>
        {present && href && (
          <a href={href} target="_blank" rel="noopener noreferrer" style={{ fontSize: "10.5px", fontFamily: "'IBM Plex Mono', monospace", color: "#1a5fb4", textDecoration: "none", whiteSpace: "nowrap" }}>
            {hrefLabel ?? "source"} ↗
          </a>
        )}
      </div>
      {present ? (
        children
      ) : (
        <div style={{ fontSize: "11.5px", color: "#8a92a0", fontFamily: "'IBM Plex Mono', monospace" }}>{absentNote}</div>
      )}
    </div>
  );
}

function Bar({ frac, color }: { frac: number; color: string }) {
  return (
    <div style={{ height: "6px", background: "#e6e9ee", borderRadius: "4px", overflow: "hidden", flex: 1 }}>
      <div style={{ height: "100%", width: Math.round(Math.max(0, Math.min(1, frac)) * 100) + "%", background: color, borderRadius: "4px" }} />
    </div>
  );
}

export default function ExternalCorroborationPanel({ t }: { t: RealTarget }) {
  const ee = t.externalEvidence;
  const gwas = ee?.gwas ?? null;
  const str = ee?.string ?? null;
  const hiv = ee?.hiv ?? null;

  if (!ee || (!gwas && !str && !hiv)) {
    return (
      <SectionCard title="External corroboration" source="src: Level-4 external revalidation (independent sources)">
        <UnknownNotice>
          no external hit — this gene is not covered by any of the three independent revalidation tracks (Open Targets GWAS · STRING · GEO GSE318876 HIV screen)
        </UnknownNotice>
      </SectionCard>
    );
  }

  // HIV-screen concordance framing: a "hit" in the external CRISPRa/n screen is
  // independent corroboration that the gene moves an immune phenotype; a
  // "present_no_hit" is honest — the gene was screened but not called.
  const hivHit = hiv?.hivHitClass && hiv.hivHitClass !== "present_no_hit";
  const gaScore = gwas?.topImmuneGAScore ?? null;
  const gaHasImmune = gaScore != null && gaScore > 0;

  return (
    <SectionCard title="External corroboration" source="src: Level-4 external revalidation (independent sources)">
      <p style={{ fontSize: "12px", lineHeight: 1.5, color: "#6b7280", margin: "-4px 0 14px" }}>
        Three <strong>independent</strong> external sources re-checked for this target — distinct from the Open Targets disease-association
        weight in the scoring panel. Each is shown honestly, with a source link when present and a "no external hit" state when absent.
      </p>
      <div style={{ display: "flex", flexDirection: "column", gap: "10px" }}>
        {/* Track A — Open Targets GWAS genetic association */}
        <Track
          label="GWAS genetic association (Open Targets)"
          present={!!gwas}
          href={t.ensembl ? `${OT}${t.ensembl}/associations` : OT}
          hrefLabel="Open Targets"
          absentNote="no external hit — not among the 55 GWAS-rechecked targets"
        >
          <div style={{ display: "flex", flexDirection: "column", gap: "8px" }}>
            <div style={{ display: "flex", alignItems: "center", gap: "12px" }}>
              <span style={{ fontSize: "11.5px", color: "#6b7280", width: "150px", flexShrink: 0 }}>Top immune-disease GA score</span>
              {gaHasImmune ? (
                <>
                  <Bar frac={gaScore!} color="#6b40b8" />
                  <span style={{ fontSize: "12.5px", fontWeight: 700, fontFamily: "'IBM Plex Mono', monospace", color: "#6b40b8", width: "42px", textAlign: "right" }}>{gaScore!.toFixed(2)}</span>
                </>
              ) : (
                <span style={{ fontSize: "11.5px", color: "#8a92a0", fontFamily: "'IBM Plex Mono', monospace" }}>no immune GWAS association</span>
              )}
            </div>
            {gwas?.topImmuneDisease && (
              <div style={{ fontSize: "12px", color: "#4a515e" }}>
                Top immune disease: <strong>{gwas.topImmuneDisease}</strong>
              </div>
            )}
            {gwas?.hasClassicAutoimmune && gwas.classicAutoimmuneHit && (
              <div style={{ fontSize: "11.5px", color: "#0a6e4f", background: "#e4f3ec", borderRadius: "7px", padding: "6px 10px" }}>
                ✓ classic-autoimmune hit: {gwas.classicAutoimmuneHit}
              </div>
            )}
            {gwas && !gwas.hasClassicAutoimmune && (
              <div style={{ fontSize: "11px", color: "#8a92a0" }}>No classic-autoimmune GWAS hit.</div>
            )}
          </div>
        </Track>

        {/* Track B — STRING known-partner recovery */}
        <Track
          label="STRING partner recovery"
          present={!!str}
          href={`${STRING_URL}${encodeURIComponent(t.gene)}&species=9606`}
          hrefLabel="STRING"
          absentNote="no external hit — not among the 15 STRING-benchmarked targets"
        >
          {str && (
            <div style={{ display: "flex", flexDirection: "column", gap: "8px" }}>
              <div style={{ display: "flex", alignItems: "center", gap: "12px" }}>
                <span style={{ fontSize: "11.5px", color: "#6b7280", width: "150px", flexShrink: 0 }}>Known partners recovered</span>
                <Bar frac={str.recoveryFrac ?? 0} color="#0d7d5a" />
                <span style={{ fontSize: "12.5px", fontWeight: 700, fontFamily: "'IBM Plex Mono', monospace", color: "#0d7d5a", width: "42px", textAlign: "right" }}>
                  {str.recoveryFrac != null ? Math.round(str.recoveryFrac * 100) + "%" : "—"}
                </span>
              </div>
              <div style={{ fontSize: "12px", color: "#4a515e" }}>
                <strong>{str.nInDownstream ?? "—"}</strong> of <strong>{str.nKnownPartners ?? "—"}</strong> STRING partners (confidence ≥ 700) recovered in this target's CD4 downstream set.
              </div>
            </div>
          )}
        </Track>

        {/* Track C — GEO GSE318876 independent HIV screen */}
        <Track
          label="Independent HIV screen (GEO GSE318876)"
          present={!!hiv}
          href={GEO_URL}
          hrefLabel="GEO"
          absentNote="no external hit — not present in the GSE318876 screen library"
        >
          {hiv && (
            <div style={{ display: "flex", flexDirection: "column", gap: "8px" }}>
              <div style={{ display: "flex", alignItems: "center", gap: "9px", flexWrap: "wrap" }}>
                <span
                  style={{
                    display: "inline-flex", alignItems: "center", gap: "6px", padding: "3px 10px", borderRadius: "20px", fontSize: "11.5px", fontWeight: 600,
                    color: hivHit ? "#0a6e4f" : "#5b6270", background: hivHit ? "#e4f3ec" : "#eef0f3",
                  }}
                >
                  <span style={{ width: "6px", height: "6px", borderRadius: "50%", background: hivHit ? "#0d7d5a" : "#8a92a0" }} />
                  {hivHit ? "screen hit — independent concordance" : "screened, not called a hit"}
                </span>
                {hiv.hivHitClass && (
                  <span style={{ fontSize: "11px", fontFamily: "'IBM Plex Mono', monospace", color: "#8a92a0" }}>{hiv.hivHitClass}</span>
                )}
              </div>
              <div style={{ fontSize: "12px", color: "#4a515e" }}>
                {hiv.screen ?? "GSE318876"}
                {hiv.bestLfc != null && (
                  <>
                    {" · best LFC "}
                    <span style={{ fontFamily: "'IBM Plex Mono', monospace", fontWeight: 600 }}>{hiv.bestLfc.toFixed(2)}</span>
                    {hiv.bestDir && ` (${hiv.bestDir})`}
                  </>
                )}
              </div>
            </div>
          )}
        </Track>
      </div>
      <div style={{ display: "flex", alignItems: "start", gap: "8px", marginTop: "13px", fontSize: "11px", color: "#8a92a0", lineHeight: 1.5 }}>
        <span style={{ fontFamily: "'IBM Plex Mono', monospace" }}>ⓘ</span>
        <span>These are external revalidation tracks (docs/mvp-research/level4_external_validation) — orthogonal to this repo's own screen. A "no external hit" is reported honestly, not hidden.</span>
      </div>
    </SectionCard>
  );
}
