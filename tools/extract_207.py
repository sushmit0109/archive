# -*- coding: utf-8 -*-
"""Extract Bangla Unicode text from the National Election Investigation report.

The PDF is not a scan: it carries a full text layer, but the Bangla is set in
SutonnyMJ (legacy Bijoy ANSI), so only spans in that family are transcoded.
Spans already in Unicode fonts (Kalpurush, Shonar Bangla, Vrinda, Mangal,
NirmalaUI) and Latin spans are kept verbatim.
"""
import json, sys, os, re
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import fitz
from bijoy_fix import convert

PDF = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                   "..", "pdfs", "commission-reports",
                   "16-national-election-investigation.pdf")


# Wingdings/Symbol glyphs land in the private-use area. Verified in context:
# Wingdings 0x6F is the questionnaire checkbox ("\u25a1 \u09b9\u09cd\u09af\u09be\u0981 / \u25a1 \u09a8\u09be"),
# SymbolMT 0xA3 is "<=" ("95 <= % < 100"), SymbolMT 0xA8 separates fields
# ("\u09a8\u09be\u09ae: X . \u09b8\u0982\u09b8\u09a6\u09c0\u09af\u09bc \u0986\u09b8\u09a8: Y").
SYMBOLS = {
    "\uf06f": "\u25a1",
    "\uf0a3": "\u2264",
    "\uf0a8": "\u2022",
}


def desymbol(text):
    for k, v in SYMBOLS.items():
        text = text.replace(k, v)
    return text


def is_bijoy(font):
    return "SutonnyMJ" in font


def page_lines(page):
    """Return [(text, max_size, is_bold)] for each visual line on the page."""
    out = []
    for b in page.get_text("dict")["blocks"]:
        for l in b.get("lines", []):
            # Group consecutive spans by encoding so a word split across
            # spans is transcoded as one unit, not letter by letter.
            runs, size, bold = [], 0.0, False
            for s in l["spans"]:
                t = s["text"]
                if not t:
                    continue
                f = s["font"].split("+")[-1]
                bij = is_bijoy(f)
                if runs and runs[-1][0] == bij:
                    runs[-1][1] += t
                else:
                    runs.append([bij, t])
                if s["size"] > size:
                    size = s["size"]
                if "Bold" in f:
                    bold = True
            txt = desymbol(
                "".join(convert(t) if bij else t for bij, t in runs)).strip()
            if txt:
                out.append((txt, round(size, 1), bold))
    return out


def main():
    doc = fitz.open(PDF)
    pages = []
    for i, p in enumerate(doc):
        pages.append({"page": i + 1, "lines": page_lines(p)})
    json.dump(pages, open(sys.argv[1], "w"), ensure_ascii=False)
    total = sum(len(l[0]) for pg in pages for l in pg["lines"])
    print(f"pages={len(pages)} chars={total:,}")


if __name__ == "__main__":
    main()
