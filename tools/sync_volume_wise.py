# -*- coding: utf-8 -*-
"""Mirror filled paragraphs into the volume-wise files the portal reads.

Commissions flagged `hasVolume` in books.json (54, 154, 206) are rendered from
volume-wise-commission-<id>.json, not chapters-commission-<id>.json -- see
loadVolumeWise() in js/site.js. Both files carry the same section ids, so
paragraphs filled in the chapters file are copied across by id.

Usage:  python3 tools/sync_volume_wise.py [--write]
"""
import json, os, sys

API = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..",
                   "reform-site", "api-data")


def main():
    write = "--write" in sys.argv
    books = json.load(open(os.path.join(API, "books.json")))
    total = 0
    for book in books:
        if not book.get("hasVolume"):
            continue
        cid = book["id"]
        cpath = os.path.join(API, f"chapters-commission-{cid}.json")
        vpath = os.path.join(API, f"volume-wise-commission-{cid}.json")
        if not (os.path.exists(cpath) and os.path.exists(vpath)):
            continue
        chapters = json.load(open(cpath))
        source = {s["id"]: s.get("paragraphs") or []
                  for ch in chapters for s in (ch.get("sections") or [])}
        volumes = json.load(open(vpath))
        copied = 0
        for vol in volumes:
            for ch in vol.get("chapters") or []:
                for sec in ch.get("sections") or []:
                    if sec.get("paragraphs"):
                        continue
                    paras = source.get(sec["id"])
                    if paras:
                        sec["paragraphs"] = paras
                        copied += 1
        chars = sum(len(p.get("content") or "")
                    for vol in volumes for ch in (vol.get("chapters") or [])
                    for s in (ch.get("sections") or []) for p in (s.get("paragraphs") or []))
        print(f"  commission {cid}: copied {copied} sections -> {chars:,} chars total")
        total += copied
        if write and copied:
            json.dump(volumes, open(vpath, "w"), ensure_ascii=False)
    print(f"\nsections synced: {total}" + ("" if write else "  (dry run -- pass --write)"))


if __name__ == "__main__":
    main()
