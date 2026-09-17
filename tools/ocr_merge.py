# -*- coding: utf-8 -*-
"""Merge the OCR ledger (and extracted figures) into the portal's chapter JSON.

Reads the ledger written by ocr_run.py (section id -> OCR'd page texts) and,
when given --blocks, the figure placements from ocr_images.py. Pages that carry
a figure use the block ordering (text and images interleaved by position on the
page); every other page is split on blank lines as before.

Each section's result is scored with the detectors in classify_pdf; a section
that still reads as garbled is skipped and reported rather than published.

Usage:
  python3 tools/ocr_merge.py --ledger ledger.json [--blocks blocks.json]
                             [--write] [--force] [--only 204]
"""
import argparse, json, os, re, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from classify_pdf import garble_verdict, word_score, bangla_words

API = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..",
                   "reform-site", "api-data")

PAGE_NO = re.compile(r"^[০-৯0-9ivxlcIVXLC\s.\-|/]+$")
NOISE = re.compile(r"^(CamScanner|Scanned (with|by)[^\n]{0,40}|Page\s*\d+)$", re.I)
JUNK = re.compile(r"^[^\wঀ-৿]{4,}$")
# Tesseract reads a figure's frame as stray rule characters before the caption;
# only strip a leading run that actually contains one of them.
FRAME = re.compile(r"^(?=[^\w]{0,4}[_|])[\s_|~^\-–—xX×]{2,10}")


# A table of contents' dot leaders come back as long runs of repeated
# characters or strings of Bengali digits. Neither Bengali nor English
# legitimately repeats a character four times, so these are safe to collapse.
RUN = re.compile(r"(.)\1{3,}")
# Contiguous and >=12 so a real date like ৩১-১০-২০২৪ (10 chars) survives.
LEADER = re.compile(r"[.\-\u2013\u2014\u09e6-\u09ef]{12,}")
# Explicit ranges: Python's \w does not reliably cover Bengali combining marks.
WORDISH = re.compile(r"[A-Za-z\u0980-\u09FF]{3,}")


# Leader debris survives as a string of short digit tokens; five or more in a
# row is a dotted line, not data.
DIGIT_DEBRIS = re.compile(
    r"(?:[\u09e6-\u09ef]{1,6}[\s.\-]+){4,}[\u09e6-\u09ef]{1,6}")


def denoise(text):
    text = RUN.sub(" ", text)
    text = LEADER.sub(" ... ", text)
    text = DIGIT_DEBRIS.sub(" ... ", text)
    text = re.sub(r"(?:\.\.\.\s*){2,}", "... ", text)
    return re.sub(r"\s{2,}", " ", text).strip()


def is_noise(text):
    """A long line carrying almost no real words is OCR debris, not content."""
    return len(text) >= 40 and len(WORDISH.findall(text)) < 3


def clean_line(text):
    text = FRAME.sub("", text)
    text = denoise(text)
    return re.sub(r"[ \t]+", " ", text).strip()


def keep(line):
    return bool(line) and not (PAGE_NO.match(line) or NOISE.match(line)
                               or JUNK.match(line) or is_noise(line))


def blocks_to_items(blocks):
    """[(text, image_filename_or_None)] from one page's ordered blocks."""
    out = []
    for b in blocks:
        if b["t"] == "img":
            out.append(("", b["v"]))
        else:
            t = clean_line(b["v"])
            if keep(t):
                out.append((t, None))
    return out


def page_to_items(page):
    """[(text, None)] from one page of plain OCR text, split on blank lines."""
    out = []
    for chunk in re.split(r"\n\s*\n", page):
        lines = [clean_line(l) for l in chunk.splitlines()]
        lines = [l for l in lines if keep(l)]
        if not lines:
            continue
        text = re.sub(r"[ \t]+", " ", " ".join(lines)).strip()
        if len(text) >= 2:
            out.append((text, None))
    return out


def section_items(pages, page_blocks):
    items = []
    for i, page in enumerate(pages):
        blk = (page_blocks or {}).get(str(i))
        items.extend(blocks_to_items(blk) if blk else page_to_items(page))
    return items


def make_paragraphs(items, start_id):
    paras = []
    for i, (text, img) in enumerate(items):
        paras.append({
            "id": start_id + i, "header": "", "serial": i + 1, "content": text,
            "hasIndex": False, "indexType": None, "indexChar": "",
            "fileName": img, "fileContentName": None, "fileContentType": None,
            "hasImage": bool(img), "image": None,
        })
    return paras


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--ledger", required=True)
    ap.add_argument("--blocks", help="figure placements from ocr_images.py")
    ap.add_argument("--only", help="comma-separated commission ids")
    ap.add_argument("--write", action="store_true")
    ap.add_argument("--force", action="store_true",
                    help="rebuild sections already filled from this ledger")
    args = ap.parse_args()

    only = {int(x) for x in args.only.split(",")} if args.only else None
    ledger = json.load(open(args.ledger))
    blocks = json.load(open(args.blocks)) if args.blocks else {}

    by_cid = {}
    for sid, rec in ledger.items():
        if only and rec["cid"] not in only:
            continue
        by_cid.setdefault(rec["cid"], {})[int(sid)] = rec

    filled, skipped, total_imgs = [], [], 0
    for cid, secs in sorted(by_cid.items()):
        path = os.path.join(API, f"chapters-commission-{cid}.json")
        chapters = json.load(open(path))
        # ids of paragraphs outside the sections we are about to rebuild
        others = [p["id"] for ch in chapters for s in ch["sections"]
                  for p in (s["paragraphs"] or [])
                  if s["id"] not in secs]
        pid = (max(others) if others else 0) + 1
        changed = False
        for ch in chapters:
            for sec in ch["sections"]:
                if sec["id"] not in secs:
                    continue
                if sec.get("paragraphs") and not args.force:
                    continue
                rec = secs[sec["id"]]
                items = section_items(rec["pages"],
                                      blocks.get(str(sec["id"])))
                joined = " ".join(t for t, _ in items if t)
                verdict, nums = garble_verdict(joined)
                if verdict == "garbled" or not items:
                    skipped.append((cid, rec["name"],
                                    verdict if items else "EMPTY", nums))
                    continue
                paras = make_paragraphs(items, pid)
                pid += len(paras)
                sec["paragraphs"] = paras
                changed = True
                nimg = sum(1 for p in paras if p["hasImage"])
                total_imgs += nimg
                bn = " ".join(bangla_words(joined))
                filled.append((cid, rec["name"], len(paras), len(joined), nimg,
                               round(word_score(bn), 1) if bn else 0, verdict))
        if changed and args.write:
            json.dump(chapters, open(path, "w"), ensure_ascii=False)

    for cid, nm, n, c, ni, sc, v in filled:
        flag = "  <-- SUSPECT" if v == "suspect" else ""
        print(f"  c{cid:<4} paras={n:>5} chars={c:>8,} imgs={ni:>4} "
              f"bnscore={sc:<5} {str(nm)[:34]}{flag}")
    print(f"\nfilled: {len(filled)} sections, {sum(x[3] for x in filled):,} chars, "
          f"{total_imgs:,} figures")
    if skipped:
        print(f"skipped: {len(skipped)}")
        for cid, nm, why, nums in skipped:
            print(f"   c{cid:<4} {why:<9} {nums} {str(nm)[:44]}")
    if not args.write:
        print("\n(dry run -- pass --write to save, then sync volume-wise files)")


if __name__ == "__main__":
    main()
