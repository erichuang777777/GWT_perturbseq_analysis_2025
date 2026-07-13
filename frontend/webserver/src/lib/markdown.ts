// Minimal, dependency-free Markdown -> HTML renderer for the embedded English
// docs (manuscript, known-limitations). It deliberately supports only the
// subset those documents use: ATX headings, bold/italic, inline code, links,
// unordered/ordered lists, horizontal rules, and paragraphs. All input is
// HTML-escaped BEFORE any markup is applied, so a doc can never inject markup
// or script -- the only tags emitted are the ones this function generates.

function escapeHtml(s: string): string {
  return s
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;");
}

// Inline spans, applied to already-escaped text.
function inline(s: string): string {
  return s
    // inline code
    .replace(/`([^`]+)`/g, '<code style="font-family:\'IBM Plex Mono\',monospace;background:#f2f3f6;padding:1px 5px;border-radius:5px;font-size:.9em">$1</code>')
    // links [text](url) -- only http(s) urls
    .replace(/\[([^\]]+)\]\((https?:\/\/[^)\s]+)\)/g, '<a href="$2" target="_blank" rel="noopener noreferrer" style="color:#1a5fb4">$1</a>')
    // bold
    .replace(/\*\*([^*]+)\*\*/g, "<strong>$1</strong>")
    // italic (single * not part of **)
    .replace(/(^|[^*])\*([^*]+)\*/g, "$1<em>$2</em>");
}

export function renderMarkdown(src: string): string {
  const lines = escapeHtml(src).split("\n");
  const out: string[] = [];
  let inUl = false;
  let inOl = false;
  let para: string[] = [];

  const flushPara = () => {
    if (para.length) {
      out.push(`<p style="margin:0 0 14px">${inline(para.join(" "))}</p>`);
      para = [];
    }
  };
  const closeLists = () => {
    if (inUl) { out.push("</ul>"); inUl = false; }
    if (inOl) { out.push("</ol>"); inOl = false; }
  };

  for (const raw of lines) {
    const line = raw.replace(/\s+$/, "");
    if (!line.trim()) { flushPara(); closeLists(); continue; }

    const h = line.match(/^(#{1,6})\s+(.*)$/);
    if (h) {
      flushPara(); closeLists();
      const lvl = h[1].length;
      const sizes = [26, 21, 17, 15, 14, 13];
      const mt = lvl <= 2 ? 28 : 20;
      out.push(`<h${lvl} style="font-size:${sizes[lvl - 1]}px;font-weight:700;margin:${mt}px 0 10px;letter-spacing:-.3px">${inline(h[2])}</h${lvl}>`);
      continue;
    }
    if (/^(-{3,}|\*{3,}|_{3,})$/.test(line.trim())) {
      flushPara(); closeLists();
      out.push('<hr style="border:none;border-top:1px solid #e2e5ea;margin:22px 0" />');
      continue;
    }
    const ul = line.match(/^\s*[-*]\s+(.*)$/);
    if (ul) {
      flushPara();
      if (inOl) { out.push("</ol>"); inOl = false; }
      if (!inUl) { out.push('<ul style="margin:0 0 14px;padding-left:22px;line-height:1.7">'); inUl = true; }
      out.push(`<li>${inline(ul[1])}</li>`);
      continue;
    }
    const ol = line.match(/^\s*\d+\.\s+(.*)$/);
    if (ol) {
      flushPara();
      if (inUl) { out.push("</ul>"); inUl = false; }
      if (!inOl) { out.push('<ol style="margin:0 0 14px;padding-left:22px;line-height:1.7">'); inOl = true; }
      out.push(`<li>${inline(ol[1])}</li>`);
      continue;
    }
    // plain text -> accumulate into a paragraph
    if (inUl || inOl) closeLists();
    para.push(line.trim());
  }
  flushPara();
  closeLists();
  return out.join("\n");
}
