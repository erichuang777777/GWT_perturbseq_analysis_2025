// Shared full-page loading/error/empty states. Consolidates: main.tsx's
// bespoke pulse-dot loader, Gallery's "Centered" helper, and the plain-text
// Suspense fallbacks in App.tsx -- previously three slightly different
// implementations of the same idea.
export function FullScreen({ children }: { children: React.ReactNode }) {
  return (
    <div
      style={{
        minHeight: "100vh",
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        fontFamily: "'IBM Plex Mono', ui-monospace, monospace",
        color: "#4a515e",
        fontSize: "14px",
      }}
    >
      {children}
    </div>
  );
}

export function InlineScreen({ children }: { children: React.ReactNode }) {
  return (
    <main style={{ flex: 1, display: "flex", alignItems: "center", justifyContent: "center", color: "#9aa1ad", fontSize: "14px", minHeight: "50vh" }}>
      {children}
    </main>
  );
}

export function LoadingPulse({ label }: { label: string }) {
  return (
    <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
      <span
        style={{
          width: "8px",
          height: "8px",
          borderRadius: "50%",
          background: "#1a5fb4",
          animation: "cd4-pulse 1s ease-in-out infinite",
        }}
      />
      {label}
      <style>{`@keyframes cd4-pulse { 0%, 100% { opacity: .3; } 50% { opacity: 1; } }`}</style>
    </div>
  );
}

export function ErrorNotice({ title, detail }: { title: string; detail: string }) {
  return (
    <div style={{ textAlign: "center", maxWidth: "420px" }}>
      <div style={{ fontWeight: 600, color: "#8a2f2f", marginBottom: "6px" }}>{title}</div>
      <div>{detail}</div>
    </div>
  );
}
