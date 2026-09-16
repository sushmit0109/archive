# -*- coding: utf-8 -*-
"""OCR the reform-commission sections that have no recoverable text layer.

For each section PDF with an empty `paragraphs` array whose text layer is
missing or corrupt (see classify_pdf), rasterize every page at 300 DPI and run
Tesseract (ben+eng, since some annexes are English). Output goes to a JSON
ledger keyed by section id -- reviewed and scored before anything is merged
into the portal by ocr_merge.py.

Resumable: a section already in the ledger is skipped, so an interrupted run
resumes without re-OCRing.

Usage:
  python3 tools/ocr_run.py --worklist WL.json --out ledger.json \
      [--only 203,204] [--jobs 8] [--max-pages N]
"""
import argparse, json, os, subprocess, sys, tempfile, time
from concurrent.futures import ThreadPoolExecutor

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import fitz

ATT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..",
                   "reform-site", "pdfs", "attachment")
TESSDATA = os.environ.get("TESSDATA_PREFIX")
DPI = 300
LANG = "ben+eng"


def ocr_png(args):
    """OCR one already-rendered PNG. Returns (index, text).

    PyMuPDF is not fork-safe, so rendering happens in the main process and only
    the tesseract subprocess (which releases the GIL) is parallelized here.
    """
    index, png = args
    env = dict(os.environ)
    if TESSDATA:
        env["TESSDATA_PREFIX"] = TESSDATA
    out = png[:-4]
    # one thread per tesseract; the pool provides the parallelism
    env["OMP_THREAD_LIMIT"] = "1"
    r = subprocess.run(["tesseract", png, out, "-l", LANG, "--psm", "3"],
                       capture_output=True, env=env)
    if r.returncode != 0:
        return index, ""
    try:
        return index, open(out + ".txt", encoding="utf-8").read()
    finally:
        for ext in (".png", ".txt"):
            try:
                os.remove(out + ext)
            except OSError:
                pass


def render_batch(doc, indices, workdir):
    """Rasterize a set of page indices to PNG; returns [(index, png)]."""
    out = []
    for i in indices:
        pix = doc[i].get_pixmap(dpi=DPI)
        png = os.path.join(workdir, f"pg{i:05d}.png")
        pix.save(png)
        out.append((i, png))
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--worklist", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--only", help="comma-separated commission ids")
    ap.add_argument("--jobs", type=int, default=os.cpu_count())
    ap.add_argument("--max-pages", type=int, help="cap pages per section (testing)")
    args = ap.parse_args()

    only = {int(x) for x in args.only.split(",")} if args.only else None
    work = json.load(open(args.worklist))
    ledger = json.load(open(args.out)) if os.path.exists(args.out) else {}

    todo = [t for t in work
            if (only is None or t["cid"] in only)
            and str(t["sec_id"]) not in ledger]
    total_pages = sum(min(t["pages"], args.max_pages or t["pages"]) for t in todo)
    print(f"sections to do: {len(todo)}  pages: {total_pages:,}  jobs: {args.jobs}")

    done_pages = 0
    t_start = time.time()
    with ThreadPoolExecutor(max_workers=args.jobs) as pool:
        for t in todo:
            pdf = os.path.join(ATT, t["pdf"])
            npages = t["pages"] if not args.max_pages else min(t["pages"], args.max_pages)
            t0 = time.time()
            # Render+OCR in batches so temp PNGs stay bounded even for a
            # 2,700-page section: render a batch serially, OCR it in parallel.
            batch = max(args.jobs * 3, 12)
            page_text = {}
            doc = fitz.open(pdf)
            with tempfile.TemporaryDirectory() as td:
                for start in range(0, npages, batch):
                    idxs = range(start, min(start + batch, npages))
                    pngs = render_batch(doc, idxs, td)
                    for i, txt in pool.map(ocr_png, pngs):
                        page_text[i] = txt
            doc.close()
            pages = [page_text.get(i, "") for i in range(npages)]
            ledger[str(t["sec_id"])] = {
                "cid": t["cid"], "pdf": t["pdf"], "name": t["name"],
                "kind": t["kind"], "pages": pages,
            }
            json.dump(ledger, open(args.out, "w"), ensure_ascii=False)
            done_pages += npages
            dt = time.time() - t0
            elapsed = time.time() - t_start
            rate = done_pages / elapsed if elapsed else 0
            eta = (total_pages - done_pages) / rate if rate else 0
            chars = sum(len(p) for p in pages)
            print(f"  c{t['cid']:<4} {npages:>4}p {dt:>5.0f}s  {chars:>8,} chars  "
                  f"[{done_pages}/{total_pages} pages, ETA {eta/60:.0f}m]  "
                  f"{t['name'][:38]}")
    print(f"\ndone in {(time.time()-t_start)/60:.1f} min")


if __name__ == "__main__":
    main()
