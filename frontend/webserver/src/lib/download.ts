// Real client-side file export via a Blob + object URL -- no backend, no
// fake alert() stub. Used for the per-gene dossier export and any future
// "export this view" action.
export function downloadFile(filename: string, content: string, mime: string): void {
  const blob = new Blob([content], { type: mime });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = filename;
  document.body.appendChild(a);
  a.click();
  a.remove();
  URL.revokeObjectURL(url);
}

export function downloadJson(filename: string, data: unknown) {
  downloadFile(filename, JSON.stringify(data, null, 2), "application/json");
}

// Minimal, RFC-4180-ish CSV: quote fields containing comma, quote or newline,
// and double up embedded quotes. `columns` is an ordered list of [header, accessor].
export function toCSV<T>(rows: T[], columns: Array<[string, (row: T) => unknown]>): string {
  const esc = (v: unknown): string => {
    const s = v == null ? "" : String(v);
    return /[",\n]/.test(s) ? `"${s.replace(/"/g, '""')}"` : s;
  };
  const header = columns.map(([h]) => esc(h)).join(",");
  const body = rows.map((r) => columns.map(([, get]) => esc(get(r))).join(",")).join("\n");
  return header + "\n" + body + "\n";
}
