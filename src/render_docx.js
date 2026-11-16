// Render a JSON document spec to .docx: numbered, hyperlinked citations; bookmarked references; figures; tables; TOC.
const fs = require("fs");
const {
  Document, Packer, Paragraph, TextRun, HeadingLevel, AlignmentType, ImageRun, Table, TableRow, TableCell, WidthType, ShadingType,
  ExternalHyperlink, InternalHyperlink, Bookmark, TableOfContents, PageBreak, Footer, PageNumber, LevelFormat, BorderStyle, VerticalAlign
} = require("docx");
const spec = JSON.parse(fs.readFileSync(process.argv[2], "utf8"));
const out = process.argv[3];
const FONT = spec.font || "Calibri";
const INK = "1A1A1A", LINK = "1C5CAB", MUTED = "52514E";
const PAGE_W = 12240, MARGIN = 1300, TEXT_W = PAGE_W - 2 * MARGIN;

function runs(segs, base = {}) {
  // segs: [{t, b, i, sup, sub}] | {cite:[n..]} | {link:url, t} | {xref:bookmark, t}
  const outRuns = [];
  for (const s of segs) {
    if (typeof s === "string") { outRuns.push(new TextRun({ text: s, font: FONT, ...base })); continue; }
    if (s.cite) {
      outRuns.push(new TextRun({ text: "[", font: FONT, ...base }));
      s.cite.forEach((n, k) => {
        if (k > 0) outRuns.push(new TextRun({ text: ", ", font: FONT, ...base }));
        outRuns.push(new InternalHyperlink({ anchor: `ref${n}`, children: [new TextRun({ text: String(n), font: FONT, color: LINK, ...base })] }));
      });
      outRuns.push(new TextRun({ text: "]", font: FONT, ...base }));
      continue;
    }
    if (s.link) { outRuns.push(new ExternalHyperlink({ link: s.link, children: [new TextRun({ text: s.t, font: FONT, color: LINK, underline: {}, ...base })] })); continue; }
    if (s.xref) { outRuns.push(new InternalHyperlink({ anchor: s.xref, children: [new TextRun({ text: s.t, font: FONT, color: LINK, ...base })] })); continue; }
    outRuns.push(new TextRun({ text: s.t, bold: s.b || base.bold, italics: s.i || base.italics, superScript: s.sup, subScript: s.sub, font: FONT, size: base.size, color: base.color }));
  }
  return outRuns;
}
function cell(text, w, opts = {}) {
  const segs = Array.isArray(text) ? text : [{ t: String(text) }];
  return new TableCell({
    width: { size: w, type: WidthType.DXA }, verticalAlign: VerticalAlign.CENTER,
    shading: opts.head ? { type: ShadingType.CLEAR, color: "auto", fill: "EFEEEA" } : undefined,
    margins: { top: 40, bottom: 40, left: 80, right: 80 },
    children: [new Paragraph({ alignment: opts.align || AlignmentType.LEFT, children: runs(segs, { size: opts.size || 16, bold: !!opts.head }) })]
  });
}
const children = [];
let numInst = 0, prevK = "";
for (const b of spec.blocks) {
  if (b.k === "num" && prevK !== "num") numInst++;
  prevK = b.k;
  switch (b.k) {
    case "title": children.push(new Paragraph({ alignment: AlignmentType.LEFT, spacing: { after: 160 }, children: runs(b.s, { size: 40, bold: true, color: INK }) })); break;
    case "subtitle": children.push(new Paragraph({ spacing: { after: 160 }, children: runs(b.s, { size: 26, color: MUTED }) })); break;
    case "meta": children.push(new Paragraph({ spacing: { after: 60 }, children: runs(b.s, { size: 20, color: MUTED }) })); break;
    case "h1": children.push(new Paragraph({ heading: HeadingLevel.HEADING_1, pageBreakBefore: !!b.pb, spacing: { before: 280, after: 120 }, children: b.bm ? [new Bookmark({ id: b.bm, children: runs(b.s) })] : runs(b.s) })); break;
    case "h2": children.push(new Paragraph({ heading: HeadingLevel.HEADING_2, spacing: { before: 200, after: 80 }, children: b.bm ? [new Bookmark({ id: b.bm, children: runs(b.s) })] : runs(b.s) })); break;
    case "h3": children.push(new Paragraph({ heading: HeadingLevel.HEADING_3, spacing: { before: 160, after: 60 }, children: runs(b.s) })); break;
    case "p": children.push(new Paragraph({ alignment: AlignmentType.JUSTIFIED, spacing: { after: 120, line: 288 }, children: runs(b.s, { size: 22 }) })); break;
    case "small": children.push(new Paragraph({ spacing: { after: 80 }, children: runs(b.s, { size: 18, color: MUTED }) })); break;
    case "bullet": children.push(new Paragraph({ numbering: { reference: "bul", level: 0 }, spacing: { after: 60, line: 276 }, children: runs(b.s, { size: 22 }) })); break;
    case "num": children.push(new Paragraph({ numbering: { reference: "num", level: 0, instance: numInst }, spacing: { after: 60, line: 276 }, children: runs(b.s, { size: 22 }) })); break;
    case "eq": children.push(new Paragraph({ alignment: AlignmentType.CENTER, spacing: { before: 80, after: 80 }, children: [...runs(b.s, { size: 22, italics: true }), new TextRun({ text: `\t(${b.n})`, font: FONT, size: 22 })], tabStops: [{ type: "right", position: TEXT_W }] })); break;
    case "pb": children.push(new Paragraph({ children: [new PageBreak()] })); break;
    case "toc": children.push(new TableOfContents("Contents", { hyperlink: true, headingStyleRange: "1-2" })); break;
    case "fig": {
      const img = fs.readFileSync(b.path); const w = b.w || 620; const h = Math.round(w * b.ratio);
      children.push(new Paragraph({ alignment: AlignmentType.CENTER, spacing: { before: 120, after: 40 }, keepNext: true, children: [new ImageRun({ data: img, type: "png", transformation: { width: w, height: h } })] }));
      children.push(new Paragraph({ spacing: { after: 200 }, children: [new Bookmark({ id: b.bm, children: runs([{ t: b.label + ". ", b: true }]) }), ...runs(b.cap, { size: 18 })].flat() }));
      break;
    }
    case "table": {
      const tw = b.widths.reduce((a, c) => a + c, 0); const scale = TEXT_W / tw; const ws = b.widths.map(x => Math.floor(x * scale)); const tot = ws.reduce((a, c) => a + c, 0);
      children.push(new Paragraph({ spacing: { before: 160, after: 60 }, keepNext: true, children: [new Bookmark({ id: b.bm, children: runs([{ t: b.label + ". ", b: true }]) }), ...runs(b.cap, { size: 18 })].flat() }));
      const rows = [new TableRow({ tableHeader: true, children: b.head.map((h, j) => cell(h, ws[j], { head: true, size: b.size || 16 })) })];
      for (const r of b.rows) rows.push(new TableRow({ cantSplit: true, children: r.map((v, j) => cell(v, ws[j], { size: b.size || 16, align: (b.align && b.align[j] === "r") ? AlignmentType.RIGHT : AlignmentType.LEFT })) }));
      children.push(new Table({ width: { size: tot, type: WidthType.DXA }, columnWidths: ws, rows }));
      if (b.note) children.push(new Paragraph({ spacing: { before: 40, after: 160 }, children: runs(b.note, { size: 16, color: MUTED }) }));
      else children.push(new Paragraph({ spacing: { after: 120 }, children: [] }));
      break;
    }
    case "ref": children.push(new Paragraph({ spacing: { after: 80 }, indent: { left: 540, hanging: 540 }, children: [new Bookmark({ id: `ref${b.n}`, children: [new TextRun({ text: `[${b.n}]\t`, font: FONT, size: 18 })] }), ...runs(b.s, { size: 18 })] })); break;
    default: throw new Error("unknown block " + b.k);
  }
}
const doc = new Document({
  creator: spec.creator || "", title: spec.title || "", description: spec.description || "",
  styles: {
    default: { document: { run: { font: FONT, size: 22, color: INK } } },
    paragraphStyles: [
      { id: "Heading1", name: "Heading 1", basedOn: "Normal", next: "Normal", quickFormat: true, run: { size: 30, bold: true, font: FONT, color: "1C5CAB" }, paragraph: { spacing: { before: 280, after: 120 }, outlineLevel: 0 } },
      { id: "Heading2", name: "Heading 2", basedOn: "Normal", next: "Normal", quickFormat: true, run: { size: 25, bold: true, font: FONT, color: INK }, paragraph: { spacing: { before: 200, after: 80 }, outlineLevel: 1 } },
      { id: "Heading3", name: "Heading 3", basedOn: "Normal", next: "Normal", quickFormat: true, run: { size: 22, bold: true, italics: true, font: FONT, color: INK }, paragraph: { spacing: { before: 160, after: 60 }, outlineLevel: 2 } }
    ]
  },
  numbering: { config: [
    { reference: "bul", levels: [{ level: 0, format: LevelFormat.BULLET, text: "•", alignment: AlignmentType.LEFT, style: { paragraph: { indent: { left: 540, hanging: 270 } } } }] },
    { reference: "num", levels: [{ level: 0, format: LevelFormat.DECIMAL, text: "%1.", alignment: AlignmentType.LEFT, style: { paragraph: { indent: { left: 540, hanging: 360 } } } }] }] },
  features: { updateFields: true },
  sections: [{
    properties: { page: { size: { width: PAGE_W, height: 15840 }, margin: { top: 1200, bottom: 1200, left: MARGIN, right: MARGIN } } },
    footers: { default: new Footer({ children: [new Paragraph({ alignment: AlignmentType.CENTER, children: [new TextRun({ text: spec.footer || "", font: FONT, size: 16, color: MUTED }), new TextRun({ children: ["  |  ", PageNumber.CURRENT], font: FONT, size: 16, color: MUTED })] })] }) },
    children
  }]
});
Packer.toBuffer(doc).then(buf => { fs.writeFileSync(out, buf); console.log("wrote", out); });
