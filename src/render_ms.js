// Render a JSON document spec to .docx: numbered, hyperlinked citations; bookmarked references; figures; tables; TOC.
const fs = require("fs");
const {
  Document, Packer, Paragraph, TextRun, HeadingLevel, AlignmentType, ImageRun, Table, TableRow, TableCell, WidthType, ShadingType,
  ExternalHyperlink, InternalHyperlink, Bookmark, TableOfContents, PageBreak, Footer, PageNumber, LevelFormat, BorderStyle, VerticalAlign, LineNumberRestartFormat
} = require("docx");
const spec = JSON.parse(fs.readFileSync(process.argv[2], "utf8"));
const out = process.argv[3];
const FONT = "Times New Roman";
const INK = "000000", LINK = "1C5CAB", MUTED = "333333";
const PAGE_W = 12240, MARGIN = 1440, TEXT_W = PAGE_W - 2 * MARGIN;
const RULE = { style: BorderStyle.SINGLE, size: 8, color: "000000" }, NONE = { style: BorderStyle.NONE, size: 0, color: "FFFFFF" };

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
    borders: { top: opts.head ? RULE : NONE, bottom: (opts.head || opts.last) ? RULE : NONE, left: NONE, right: NONE },
    margins: { top: 20, bottom: 20, left: 80, right: 80 },
    children: [new Paragraph({ alignment: opts.align || AlignmentType.LEFT, spacing: { line: 240 }, children: runs(segs, { size: opts.size || 18, bold: !!opts.head }) })]
  });
}
const children = [];
let numInst = 0, prevK = "", afterHead = true;
for (const b of spec.blocks) {
  if (b.k === "num" && prevK !== "num") numInst++;
  afterHead = ["h1", "h2", "h3", "title", "meta", "fig", "table", "eq"].includes(prevK) || prevK === "";
  prevK = b.k;
  switch (b.k) {
    case "title": children.push(new Paragraph({ alignment: AlignmentType.CENTER, spacing: { after: 240, line: 360 }, children: runs(b.s, { size: 28, bold: true, color: INK }) })); break;
    case "subtitle": children.push(new Paragraph({ spacing: { after: 160 }, children: runs(b.s, { size: 26, color: MUTED }) })); break;
    case "meta": children.push(new Paragraph({ alignment: AlignmentType.CENTER, spacing: { after: 60, line: 276 }, children: runs(b.s, { size: b.big ? 24 : 20, color: INK }) })); break;
    case "h1": children.push(new Paragraph({ heading: HeadingLevel.HEADING_1, pageBreakBefore: !!b.pb, spacing: { before: 360, after: 120, line: 480 }, children: b.bm ? [new Bookmark({ id: b.bm, children: runs(b.s, { size: 24, bold: true }) })] : runs(b.s, { size: 24, bold: true }) })); break;
    case "h2": children.push(new Paragraph({ heading: HeadingLevel.HEADING_2, spacing: { before: 240, after: 120, line: 480 }, children: b.bm ? [new Bookmark({ id: b.bm, children: runs(b.s, { size: 24, bold: true }) })] : runs(b.s, { size: 24, bold: true }) })); break;
    case "h3": children.push(new Paragraph({ heading: HeadingLevel.HEADING_3, spacing: { before: 160, after: 60 }, children: runs(b.s) })); break;
    case "p": children.push(new Paragraph({ alignment: AlignmentType.JUSTIFIED, indent: afterHead ? undefined : { firstLine: 720 }, spacing: { after: 0, line: 480 }, children: runs(b.s, { size: 24 }) })); break;
    case "small": children.push(new Paragraph({ spacing: { before: 120, after: 120, line: 480 }, children: runs(b.s, { size: 24 }) })); break;
    case "bullet": children.push(new Paragraph({ numbering: { reference: "bul", level: 0 }, spacing: { after: 0, line: 480 }, children: runs(b.s, { size: 24 }) })); break;
    case "num": children.push(new Paragraph({ numbering: { reference: "num", level: 0, instance: numInst }, spacing: { after: 0, line: 480 }, children: runs(b.s, { size: 24 }) })); break;
    case "eq": children.push(new Paragraph({ alignment: AlignmentType.LEFT, spacing: { before: 120, after: 120, line: 360 }, children: [new TextRun({ text: "\t", font: FONT }), ...runs(b.s, { size: 24, italics: true }), new TextRun({ text: `\t(${b.n})`, font: FONT, size: 24 })], tabStops: [{ type: "center", position: Math.round(TEXT_W / 2) }, { type: "right", position: TEXT_W }] })); break;
    case "pb": children.push(new Paragraph({ children: [new PageBreak()] })); break;
    case "toc": children.push(new TableOfContents("Contents", { hyperlink: true, headingStyleRange: "1-2" })); break;
    case "fig": {
      const img = fs.readFileSync(b.path); const w = b.w || 620; const h = Math.round(w * b.ratio);
      children.push(new Paragraph({ alignment: AlignmentType.CENTER, spacing: { before: 240, after: 60 }, keepNext: true, children: [new ImageRun({ data: img, type: "png", transformation: { width: w, height: h } })] }));
      children.push(new Paragraph({ spacing: { after: 240, line: 276 }, children: [new Bookmark({ id: b.bm, children: runs([{ t: b.label + ". ", b: true }], { size: 20 }) }), ...runs(b.cap, { size: 20 })].flat() }));
      break;
    }
    case "table": {
      const tw = b.widths.reduce((a, c) => a + c, 0); const scale = TEXT_W / tw; const ws = b.widths.map(x => Math.floor(x * scale)); const tot = ws.reduce((a, c) => a + c, 0);
      children.push(new Paragraph({ spacing: { before: 240, after: 60, line: 276 }, keepNext: true, children: [new Bookmark({ id: b.bm, children: runs([{ t: b.label + ". ", b: true }], { size: 20 }) }), ...runs(b.cap, { size: 20 })].flat() }));
      const rows = [new TableRow({ tableHeader: true, children: b.head.map((h, j) => cell(h, ws[j], { head: true, size: 18, align: (b.align && b.align[j] === "r") ? AlignmentType.RIGHT : AlignmentType.LEFT })) })];
      b.rows.forEach((r, i) => rows.push(new TableRow({ cantSplit: true, children: r.map((v, j) => cell(v, ws[j], { size: 18, last: i === b.rows.length - 1, align: (b.align && b.align[j] === "r") ? AlignmentType.RIGHT : AlignmentType.LEFT })) })));
      children.push(new Table({ width: { size: tot, type: WidthType.DXA }, columnWidths: ws, rows, borders: { top: NONE, bottom: NONE, left: NONE, right: NONE, insideHorizontal: NONE, insideVertical: NONE } }));
      if (b.note) children.push(new Paragraph({ spacing: { before: 40, after: 240, line: 276 }, children: runs(b.note, { size: 18 }) }));
      else children.push(new Paragraph({ spacing: { after: 240 }, children: [] }));
      break;
    }
    case "ref": children.push(new Paragraph({ spacing: { after: 0, line: 480 }, indent: { left: 0 }, children: [new Bookmark({ id: `ref${b.n}`, children: [new TextRun({ text: `[${b.n}] `, font: FONT, size: 24 })] }), ...runs(b.s, { size: 24 })] })); break;
    default: throw new Error("unknown block " + b.k);
  }
}
const doc = new Document({
  creator: spec.creator || "", title: spec.title || "", description: spec.description || "",
  styles: {
    default: { document: { run: { font: FONT, size: 24, color: INK } } },
    paragraphStyles: [
      { id: "Heading1", name: "Heading 1", basedOn: "Normal", next: "Normal", quickFormat: true, run: { size: 24, bold: true, font: FONT, color: "000000" }, paragraph: { spacing: { before: 280, after: 120 }, outlineLevel: 0 } },
      { id: "Heading2", name: "Heading 2", basedOn: "Normal", next: "Normal", quickFormat: true, run: { size: 24, bold: true, font: FONT, color: INK }, paragraph: { spacing: { before: 200, after: 80 }, outlineLevel: 1 } },
      { id: "Heading3", name: "Heading 3", basedOn: "Normal", next: "Normal", quickFormat: true, run: { size: 22, bold: true, italics: true, font: FONT, color: INK }, paragraph: { spacing: { before: 160, after: 60 }, outlineLevel: 2 } }
    ]
  },
  numbering: { config: [
    { reference: "bul", levels: [{ level: 0, format: LevelFormat.BULLET, text: "-", alignment: AlignmentType.LEFT, style: { paragraph: { indent: { left: 720, hanging: 360 } } } }] },
    { reference: "num", levels: [{ level: 0, format: LevelFormat.DECIMAL, text: "%1.", alignment: AlignmentType.LEFT, style: { paragraph: { indent: { left: 540, hanging: 360 } } } }] }] },
  features: { updateFields: true },
  sections: [{
    properties: { page: { size: { width: PAGE_W, height: 15840 }, margin: { top: 1440, bottom: 1440, left: MARGIN, right: MARGIN } }, lineNumbers: { countBy: 1, restart: LineNumberRestartFormat.CONTINUOUS } },
    footers: { default: new Footer({ children: [new Paragraph({ alignment: AlignmentType.CENTER, children: [new TextRun({ children: [PageNumber.CURRENT], font: FONT, size: 22 })] })] }) },
    children
  }]
});
Packer.toBuffer(doc).then(buf => { fs.writeFileSync(out, buf); console.log("wrote", out); });
