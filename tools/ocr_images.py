# -*- coding: utf-8 -*-
"""Extract figures from the OCR'd section PDFs and place them in reading order.

ocr_run.py captured text only, so figures were dropped. This recovers them:
for every page that carries a content image, the page is re-OCR'd with
Tesseract's TSV output (which carries a bounding box per line), the images are
located in the same pixel space, and the two are interleaved by vertical
position. The result is a per-page list of blocks -- text paragraphs and images
in the order a reader meets them -- which ocr_merge.py turns into paragraphs.

Only pages with images are re-OCR'd; the rest keep the text already in the
ledger, so this is ~1/2 the corpus rather than all of it.

Images identical byte-for-byte are stored once and referenced from each place
they appear.

Usage:
  python3 tools/ocr_images.py --worklist WL.json --out blocks.json \
      --imgdir reform-site/pdfs/attachment [--jobs 8]
"""
import argparse, csv, hashlib, io, json, os, random, subprocess, sys, tempfile, time
from concurrent.futures import ThreadPoolExecutor

import fitz

DPI = 300
SCALE = DPI / 72.0
LANG = "ben+eng"
TESSDATA = os.environ.get("TESSDATA_PREFIX")

# A picture covering most of the sheet is the scan itself, not a figure.
MAX_AREA_FRAC = 0.75
MIN_SIDE_PT = 60


def content_images(page):
    """Image placements on this page that look like figures, not page scans."""
    parea = abs(page.rect.width * page.rect.height) or 1.0
    out = []
    for info in page.get_image_info(xrefs=True):
        x0, y0, x1, y1 = info["bbox"]
        w, h = abs(x1 - x0), abs(y1 - y0)
        if w < MIN_SIDE_PT or h < MIN_SIDE_PT:
            continue
        if (w * h) / parea >= MAX_AREA_FRAC:
            continue
        if not info.get("xref"):
            continue
        out.append({"xref": info["xref"], "bbox": (x0, y0, x1, y1)})
    return out


def tsv_paragraphs(png):
    """Run Tesseract for TSV and return [(top_px, text)] paragraphs."""
    env = dict(os.environ)
    if TESSDATA:
        env["TESSDATA_PREFIX"] = TESSDATA
    env["OMP_THREAD_LIMIT"] = "1"
    base = png[:-4] + "_tsv"
    # -c rather than the "tsv" config file: TESSDATA_PREFIX here holds only the
    # language data, not Tesseract's configs/ directory.
    r = subprocess.run(["tesseract", png, base, "-l", LANG, "--psm", "3",
                        "-c", "tessedit_create_tsv=1"],
                       capture_output=True, env=env)
    path = base + ".tsv"
    if r.returncode != 0 or not os.path.exists(path):
        return []
    paras = {}
    with open(path, encoding="utf-8", errors="replace") as fh:
        for row in csv.DictReader(fh, delimiter="\t", quoting=csv.QUOTE_NONE):
            try:
                if int(row["level"]) != 5:
                    continue
                conf = float(row["conf"])
            except (ValueError, KeyError, TypeError):
                continue
            word = (row.get("text") or "").strip()
            if conf < 0 or not word:
                continue
            key = (row["block_num"], row["par_num"])
            top = int(row["top"])
            slot = paras.setdefault(key, {"top": top, "words": []})
            slot["top"] = min(slot["top"], top)
            slot["words"].append(word)
    try:
        os.remove(path)
    except OSError:
        pass
    return [(v["top"], " ".join(v["words"]).strip())
            for v in paras.values() if v["words"]]


def page_blocks(args):
    """Return (section_id, page_index, [blocks]) for one image-bearing page."""
    sec_id, pdf_path, pno, imgdir, seen = args
    doc = fitz.open(pdf_path)
    page = doc[pno]
    imgs = content_images(page)
    if not imgs:
        doc.close()
        return sec_id, pno, None

    placed = []
    for im in imgs:
        try:
            raw = doc.extract_image(im["xref"])
        except Exception:
            continue
        data, ext = raw["image"], (raw.get("ext") or "png").lower()
        if ext not in ("jpeg", "jpg", "png", "gif", "webp"):
            try:
                pix = fitz.Pixmap(doc, im["xref"])
                if pix.n - pix.alpha >= 4:
                    pix = fitz.Pixmap(fitz.csRGB, pix)
                data, ext = pix.tobytes("png"), "png"
            except Exception:
                continue
        digest = hashlib.sha1(data).hexdigest()
        fname = seen.get(digest)
        if fname is None:
            fname = (f"{random.randint(10**9, 10**10 - 1)}_"
                     f"{int(time.time() * 1000)}{random.randint(10, 99)}.{ext}")
            with open(os.path.join(imgdir, fname), "wb") as fh:
                fh.write(data)
            seen[digest] = fname
        top_px = (im["bbox"][1] - page.rect.y0) * SCALE
        placed.append((top_px, fname))
    doc.close()
    if not placed:
        return sec_id, pno, None

    with tempfile.TemporaryDirectory() as td:
        png = os.path.join(td, "p.png")
        d2 = fitz.open(pdf_path)
        d2[pno].get_pixmap(dpi=DPI).save(png)
        d2.close()
        texts = tsv_paragraphs(png)

    blocks = ([{"t": "text", "y": y, "v": v} for y, v in texts]
              + [{"t": "img", "y": y, "v": f} for y, f in placed])
    blocks.sort(key=lambda b: b["y"])
    return sec_id, pno, [{"t": b["t"], "v": b["v"]} for b in blocks]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--worklist", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--imgdir", required=True)
    ap.add_argument("--jobs", type=int, default=os.cpu_count())
    ap.add_argument("--only", help="comma-separated commission ids")
    args = ap.parse_args()

    only = {int(x) for x in args.only.split(",")} if args.only else None
    work = [t for t in json.load(open(args.worklist))
            if only is None or t["cid"] in only]
    os.makedirs(args.imgdir, exist_ok=True)
    att = os.path.join("reform-site", "pdfs", "attachment")

    tasks, seen = [], {}
    for t in work:
        pdf = os.path.join(att, t["pdf"])
        doc = fitz.open(pdf)
        for pno in range(doc.page_count):
            if content_images(doc[pno]):
                tasks.append((t["sec_id"], pdf, pno, args.imgdir, seen))
        doc.close()
    print(f"pages with figures: {len(tasks)}  jobs: {args.jobs}")

    out, t0, done = {}, time.time(), 0
    with ThreadPoolExecutor(max_workers=args.jobs) as pool:
        for sec_id, pno, blocks in pool.map(page_blocks, tasks):
            done += 1
            if blocks:
                out.setdefault(str(sec_id), {})[str(pno)] = blocks
            if done % 200 == 0:
                el = time.time() - t0
                print(f"  {done}/{len(tasks)} pages  {el/60:.1f}m  "
                      f"ETA {(len(tasks)-done)*el/done/60:.0f}m")
    json.dump(out, open(args.out, "w"), ensure_ascii=False)
    nimg = sum(1 for s in out.values() for p in s.values()
               for b in p if b["t"] == "img")
    print(f"\nsections with figures: {len(out)}  placements: {nimg}  "
          f"distinct files: {len(seen)}")


if __name__ == "__main__":
    main()
