# -*- coding: utf-8 -*-
"""Merge the OCR ledger into the portal's chapter JSON.

Reads the ledger written by ocr_run.py (section id -> OCR'd page texts),
turns each section's pages into paragraphs matching the portal schema, and
writes them into chapters-commission-<id>.json for sections that are still
empty. Every section's result is scored with the same detectors used
elsewhere (classify_pdf); a section that still reads as garbled is skipped and
reported rather than published.

Usage:
  python3 tools/ocr_merge.py --ledger ledger.json [--write] [--only 204]
"""
import argparse, json, os, re, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from classify_pdf import (garble_verdict, exotic_ratio, leading_matra_pct,
                          word_score, bangla_words)

API = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..",
                   "reform-site", "api-data")

PAGE_NO = re.compile(r"^[০-৯0-9ivxlcIVXLC\s.\-|/]+$")
NOISE = re.compile(r"^(CamScanner|Scanned (with|by)[^\n]{0,40}|Page\s*\d+)$", re.I)
# Tesseract marks an unreadable region with runs of stray punctuation; drop
# lines that are mostly non-word symbols.
JUNK = re.compile(r"^[^\wঀ-৿]{4,}$")


def paragraphs_from_pages(pages):
    """Flatten OCR page texts into paragraphs split on blank lines."""
    out = []
    for page in pages:
        # normalize newlines; a blank line separates paragraphs
        blocks = re.split(r"\n\s*\n", page)
        for b in blocks:
            lines = [ln.strip() for ln in b.splitlines() if ln.strip()]
            lines = [ln for ln in lines
                     if not PAGE_NO.match(ln) and not NOISE.match(ln)
                     and not JUNK.match(ln)]
            if not lines:
                continue
            text = re.sub(r"[ \t]+", " ", " ".join(lines)).strip()
            if len(text) >= 2:
                out.append(text)
    return out


def make_paragraphs(pages, start_id):
    texts = paragraphs_from_pages(pages)
    return [{
        "id": start_id + i, "header": "", "serial": i + 1, "content": t,
        "hasIndex": False, "indexType": None, "indexChar": "",
        "fileName": None, "fileContentName": None, "fileContentType": None,
        "hasImage": False, "image": None,
    } for i, t in enumerate(texts)], texts


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--ledger", required=True)
    ap.add_argument("--only", help="comma-separated commission ids")
    ap.add_argument("--write", action="store_true")
    args = ap.parse_args()

    only = {int(x) for x in args.only.split(",")} if args.only else None
    ledger = json.load(open(args.ledger))

    # group ledger entries by commission
    by_cid = {}
    for sid, rec in ledger.items():
        if only and rec["cid"] not in only:
            continue
        by_cid.setdefault(rec["cid"], {})[int(sid)] = rec

    filled, skipped = [], []
    for cid, secs in sorted(by_cid.items()):
        path = os.path.join(API, f"chapters-commission-{cid}.json")
        chapters = json.load(open(path))
        pid = max([p["id"] for ch in chapters for s in ch["sections"]
                   for p in (s["paragraphs"] or [])] or [0]) + 1
        changed = False
        for ch in chapters:
            for sec in ch["sections"]:
                if sec.get("paragraphs") or sec["id"] not in secs:
                    continue
                rec = secs[sec["id"]]
                paras, texts = make_paragraphs(rec["pages"], pid)
                joined = " ".join(texts)
                verdict, nums = garble_verdict(joined)
                if verdict == "garbled" or not paras:
                    skipped.append((cid, rec["name"], verdict if paras else "EMPTY", nums))
                    continue
                for p in paras:
                    p["id"] = pid
                    pid += 1
                sec["paragraphs"] = paras
                changed = True
                bn = " ".join(bangla_words(joined))
                filled.append((cid, rec["name"], len(paras), len(joined),
                               round(word_score(bn), 1) if bn else 0,
                               verdict))
        if changed and args.write:
            json.dump(chapters, open(path, "w"), ensure_ascii=False)

    for cid, nm, n, c, sc, v in filled:
        flag = "  <-- SUSPECT" if v == "suspect" else ""
        print(f"  c{cid:<4} paras={n:>5} chars={c:>8,} bnscore={sc:<5} {str(nm)[:40]}{flag}")
    print(f"\nfilled: {len(filled)} sections, {sum(x[3] for x in filled):,} chars")
    if skipped:
        print(f"skipped: {len(skipped)}")
        for cid, nm, why, nums in skipped:
            print(f"   c{cid:<4} {why:<9} {nums} {str(nm)[:44]}")
    if not args.write:
        print("\n(dry run -- pass --write to save, then run sync_volume_wise.py)")


if __name__ == "__main__":
    main()
