# -*- coding: utf-8 -*-
"""Fill paragraph text for every portal section that ships as a PDF only.

Many sections across the archive (annexes, appendices, whole commissions such
as 204 and 206) were published as PDFs with an empty `paragraphs` array, so
none of their text was searchable. Each such section has its own PDF under
reform-site/pdfs/attachment/, which is exactly that section's pages.

Three kinds of source PDF turn up, and only the first needs OCR:
  SCANNED  -- no text layer at all; skipped here and reported.
  BIJOY    -- text layer set in SutonnyMJ (legacy Bijoy ANSI); transcoded.
  UNICODE  -- text layer already in Unicode Bangla; taken as-is.
A single PDF can mix Bijoy and Unicode spans, so the choice is per span.

Usage:  python3 tools/build_sections.py [--write] [--only 206,204]
"""
import collections, json, os, re, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import fitz
from bijoy_fix import convert
from classify_pdf import classify, garble_verdict

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "reform-site")
ATT = os.path.join(ROOT, "pdfs", "attachment")
API = os.path.join(ROOT, "api-data")

SYMBOLS = {"": "□", "": "≤", "": "•",
           "": "•", "": "▪"}

# Nukta letters have a precomposed and a base+nukta spelling and NFC will not
# unify them (composition exclusions), so fold before comparing.
_NUKTA = str.maketrans({"ড়": "ড়", "ঢ়": "ঢ়",
                        "য়": "য়"})
PAGE_NO = re.compile(r"^[০-৯0-9\s.\-|/]+$")
# Scanner watermarks stamped onto pages; not part of the document.
NOISE = re.compile(r"^(CamScanner|Scanned (with|by)[^\n]{0,40})$", re.I)
MIN_CPP = 100  # chars/page below this means there is no usable text layer


def fold(text):
    return re.sub(r"\s+", "", text).translate(_NUKTA)


def line_text(line):
    """Join a line's spans, transcoding each contiguous Bijoy run as a unit."""
    runs = []
    for s in line["spans"]:
        if not s["text"]:
            continue
        bij = "SutonnyMJ" in s["font"]
        if runs and runs[-1][0] == bij:
            runs[-1][1] += s["text"]
        else:
            runs.append([bij, s["text"]])
    out = []
    for bij, t in runs:
        if bij:
            t = convert(t)
        for k, v in SYMBOLS.items():
            t = t.replace(k, v)
        out.append(t)
    return "".join(out)


def paragraphs_of(doc, titles):
    """Yield paragraph strings, dropping running heads and page numbers.

    `titles` are the section/chapter names, whose repetition at the top of
    every page is a running header rather than content.
    """
    folded = [fold(t) for t in titles if t]
    seen_head = collections.Counter()
    out = []
    for page in doc:
        h = page.rect.height
        for b in page.get_text("dict")["blocks"]:
            if "lines" not in b:
                continue
            lines = [x for x in (line_text(l).strip() for l in b["lines"]) if x]
            if not lines:
                continue
            text = re.sub(r"[ \t]+", " ", " ".join(lines)).strip()
            if not text or PAGE_NO.match(text) or NOISE.match(text):
                continue
            y0, y1 = b["bbox"][1], b["bbox"][3]
            if y1 < h * 0.10 or y0 > h * 0.92:
                f = fold(text)
                if len(f) <= 90 and any(f.startswith(t[:12]) or t.startswith(f[:12])
                                        for t in folded if len(t) >= 6):
                    continue
                seen_head[f] += 1
            out.append(text)
    # A short line repeated on most pages in a header/footer band is a running
    # head even when it does not match the section title.
    repeated = {k for k, v in seen_head.items() if v >= max(3, doc.page_count * 0.5)}
    return [t for t in out if fold(t) not in repeated]


def drop_title_heading(paras, titles):
    folded = [fold(t) for t in titles if t]
    out = list(paras)
    while out:
        head = fold(out[0])
        if len(head) <= 60 and any(head == t or t.startswith(head) for t in folded):
            out.pop(0)
        else:
            break
    return out


def main():
    only = None
    for a in sys.argv:
        if a.startswith("--only"):
            only = {int(x) for x in a.split("=", 1)[1].split(",")} if "=" in a else None
    if "--only" in sys.argv:
        only = {int(x) for x in sys.argv[sys.argv.index("--only") + 1].split(",")}

    write = "--write" in sys.argv
    skipped, filled, suspect = [], [], []
    for path in sorted(__import__("glob").glob(os.path.join(API, "chapters-commission-*.json")),
                       key=lambda p: int(re.search(r"(\d+)\.json", p).group(1))):
        cid = int(re.search(r"(\d+)\.json", path).group(1))
        if only and cid not in only:
            continue
        chapters = json.load(open(path))
        pid = max([p["id"] for ch in chapters for s in ch["sections"]
                   for p in (s["paragraphs"] or [])] or [0]) + 1
        changed = False
        for ch in chapters:
            for sec in ch["sections"]:
                if sec.get("paragraphs"):
                    continue
                name = sec.get("pdfName")
                if not name:
                    continue
                f = os.path.join(ATT, name)
                if not os.path.exists(f):
                    skipped.append((cid, name, "MISSING")); continue
                doc = fitz.open(f)
                kind, stats = classify(doc)
                if kind in ("SCANNED", "EMPTY", "BROKEN", "GARBLED"):
                    skipped.append((cid, sec.get("name") or ch["title"], kind))
                    doc.close(); continue
                titles = [sec.get("name"), sec.get("nameBangla"), ch.get("title")]
                paras = drop_title_heading(paragraphs_of(doc, titles), titles)
                doc.close()
                if not paras:
                    skipped.append((cid, sec.get("name"), "NO TEXT")); continue
                # Output-side check: never publish text that does not read as
                # Bangla, whatever the input-side verdict said.
                joined = " ".join(paras)
                verdict, nums = garble_verdict(joined)
                if verdict == "garbled":
                    skipped.append((cid, sec.get("name"), f"GARBLED-OUT {nums}"))
                    continue
                if verdict == "suspect":
                    suspect.append((cid, sec.get("name"), kind, nums))
                sec["paragraphs"] = [{
                    "id": pid + i, "header": "", "serial": i + 1, "content": t,
                    "hasIndex": False, "indexType": None, "indexChar": "",
                    "fileName": None, "fileContentName": None,
                    "fileContentType": None, "hasImage": False, "image": None,
                } for i, t in enumerate(paras)]
                pid += len(paras)
                changed = True
                filled.append((cid, sec.get("name"), kind, len(paras),
                               sum(len(t) for t in paras)))
        if changed and write:
            json.dump(chapters, open(path, "w"), ensure_ascii=False)

    for cid, nm, kind, n, c in filled:
        print(f"  c{cid:<4} {kind:<8} paras={n:>5} chars={c:>9,}  {str(nm)[:46]}")
    print(f"\nfilled sections: {len(filled)}  chars={sum(x[4] for x in filled):,}")
    if suspect:
        print(f"\nSUSPECT (filled, but worth a human look): {len(suspect)}")
        for cid, nm, kind, nums in suspect:
            print(f"   c{cid:<4} {kind:<8} {nums} {str(nm)[:50]}")
    print(f"\nskipped: {len(skipped)}")
    for cid, nm, why in skipped:
        print(f"   c{cid:<4} {why:<9} {str(nm)[:60]}")
    if write:
        print("\nWROTE changes")
    else:
        print("\n(dry run -- pass --write to save)")


if __name__ == "__main__":
    main()
