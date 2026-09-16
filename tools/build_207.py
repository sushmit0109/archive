# -*- coding: utf-8 -*-
"""Fill in paragraph text for commission 207 (National Election Investigation).

The portal shipped this commission as per-chapter PDFs with empty `paragraphs`
arrays, so none of its text was searchable. Each section's own PDF is an exact
split of the chapter, so text is taken from there -- no boundary guessing.
The Bangla is SutonnyMJ (legacy Bijoy ANSI) and is transcoded by bijoy_fix.
"""
import json, os, re, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import fitz
from bijoy_fix import convert

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "reform-site")
ATT = os.path.join(ROOT, "pdfs", "attachment")
CHAPTERS = os.path.join(ROOT, "api-data", "chapters-commission-207.json")

SYMBOLS = {"": "□", "": "≤", "": "•"}

RUNNING_HEAD = "জাতীয় নির্বাচন"  # report title in the running header
BN_DIGITS = "০-৯"
# a bare page number, optionally with stray punctuation
PAGE_NO = re.compile(r"^[" + BN_DIGITS + r"0-9\s.\-]+$")


def span_text(span):
    t = span["text"]
    if "SutonnyMJ" in span["font"]:
        t = convert(t)
    for k, v in SYMBOLS.items():
        t = t.replace(k, v)
    return t


def line_text(line):
    """Join a line's spans, transcoding each contiguous same-encoding run."""
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


def blocks_of(pdf_path, chapter_title):
    """Yield paragraph strings, dropping running heads and page numbers."""
    doc = fitz.open(pdf_path)
    norm_title = re.sub(r"\s+", "", chapter_title)
    for page in doc:
        h = page.rect.height
        for b in page.get_text("dict")["blocks"]:
            if "lines" not in b:
                continue
            y0, y1 = b["bbox"][1], b["bbox"][3]
            lines = [line_text(l).strip() for l in b["lines"]]
            lines = [l for l in lines if l]
            if not lines:
                continue
            # running header band / footer band
            if y1 < h * 0.09 or y0 > h * 0.93:
                joined = re.sub(r"\s+", "", " ".join(lines))
                if (RUNNING_HEAD in joined or joined.startswith(norm_title[:14])
                        or PAGE_NO.match(" ".join(lines))):
                    continue
            if len(lines) == 1 and PAGE_NO.match(lines[0]):
                continue
            text = " ".join(lines)
            text = re.sub(r"[ \t]+", " ", text).strip()
            if text:
                yield text


ADHYAY = "\u0985\u09a7\u09cd\u09af\u09be\u09af\u09bc"  # "chapter"


# Bangla has two spellings for the nukta letters: precomposed (\u09dc \u09dd \u09df) and
# base+nukta. NFC will not unify them -- they are composition exclusions -- so
# compare on an explicitly decomposed form.
_NUKTA = str.maketrans({
    "\u09dc": "\u09a1\u09bc",
    "\u09dd": "\u09a2\u09bc",
    "\u09df": "\u09af\u09bc",
})


def fold(text):
    """Normalize for comparison: drop whitespace, unify nukta spellings."""
    return re.sub(r"\s+", "", text).translate(_NUKTA)


def drop_title_heading(paras, title):
    """Drop the leading blocks that just repeat the chapter title or
    "<ordinal> chapter" -- the portal already shows the title above."""
    norm_title = fold(title)
    out = list(paras)
    while out:
        head = fold(out[0])
        if len(head) <= 60 and (head == norm_title or ADHYAY in head
                                or norm_title.startswith(head)):
            out.pop(0)
        else:
            break
    return out


def main():
    chapters = json.load(open(CHAPTERS))
    pid = max([p["id"] for ch in chapters for s in ch["sections"]
               for p in (s["paragraphs"] or [])] or [0]) + 1
    total = 0
    for ch in chapters:
        for sec in ch["sections"]:
            if not sec.get("pdfName"):
                continue
            paras = drop_title_heading(
                blocks_of(os.path.join(ATT, sec["pdfName"]), ch["title"]),
                ch["title"])
            sec["paragraphs"] = [{
                "id": pid + i,
                "header": "",
                "serial": i + 1,
                "content": t,
                "hasIndex": False,
                "indexType": None,
                "indexChar": "",
                "fileName": None,
                "fileContentName": None,
                "fileContentType": None,
                "hasImage": False,
                "image": None,
            } for i, t in enumerate(paras)]
            pid += len(paras)
            total += sum(len(t) for t in paras)
            print(f"  {ch['serial']:>2}. {ch['title'][:42]:<44} "
                  f"paragraphs={len(paras):>5} chars={sum(len(t) for t in paras):>8,}")
    if "--write" in sys.argv:
        json.dump(chapters, open(CHAPTERS, "w"), ensure_ascii=False)
        print(f"\nwrote {CHAPTERS}")
    print(f"TOTAL chars={total:,}")


if __name__ == "__main__":
    main()
