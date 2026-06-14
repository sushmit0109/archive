import urllib.request
import json
import os
import ssl
import sys
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

BASE = "https://reform.gov.bd"
OUT = "c:/Users/quazi/OneDrive/Desktop/gonovote/reform-site/pdfs/section-pdfs"
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

def fetch_json(url):
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "application/json"})
    with urllib.request.urlopen(req, context=ctx) as resp:
        return json.loads(resp.read().decode())

def download_pdf(pdf_name, dest_path):
    if os.path.exists(dest_path):
        return
    url = f"{BASE}/api/attachment/view-pdf/{pdf_name}"
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    try:
        with urllib.request.urlopen(req, context=ctx) as resp:
            with open(dest_path, "wb") as f:
                f.write(resp.read())
        size = os.path.getsize(dest_path)
        print(f"  OK {size:>10,} bytes -> {os.path.basename(dest_path)}")
    except Exception as e:
        print(f"  FAIL {pdf_name}: {e}")

def extract_section_pdfs(chapters, commission_dir):
    """Extract PDFs from chapter->section->hasPdf hierarchy"""
    count = 0
    for ch in chapters:
        for sec in ch.get("sections", []):
            if sec.get("hasPdf") and sec.get("pdfName"):
                pdf_name = sec["pdfName"]
                safe_name = sec.get("name", "unnamed")[:60].replace("/", "-").replace("\\", "-").replace(":", "-").strip()
                dest = os.path.join(commission_dir, f"{pdf_name.split('_')[0]}_{safe_name}.pdf")
                download_pdf(pdf_name, dest)
                count += 1
    return count

# Get all commissions
books = fetch_json(f"{BASE}/api/book/find-all")
print(f"Found {len(books)} commissions\n")

total = 0
for book in books:
    bid = book["id"]
    name = book.get("nameBangla", book.get("name", str(bid)))
    safe_name = f"{book['serial']:02d}-{book.get('name','unknown')[:40]}".replace("/","-").replace(" ","-")
    commission_dir = os.path.join(OUT, safe_name)
    os.makedirs(commission_dir, exist_ok=True)

    print(f"\n=== {name} (ID:{bid}) ===")

    if book.get("hasVolume"):
        # Fetch volume-wise chapters
        try:
            volumes = fetch_json(f"{BASE}/api/volume/by-book-volume-wise/{bid}")
            for vol in volumes:
                vol_name = vol.get("name", "volume")[:30].replace("/","-")
                vol_dir = os.path.join(commission_dir, vol_name.strip())
                os.makedirs(vol_dir, exist_ok=True)
                chapters = vol.get("chapters", [])
                if chapters:
                    cnt = extract_section_pdfs(chapters, vol_dir)
                    total += cnt
        except Exception as e:
            print(f"  Volume fetch error: {e}")
    else:
        # Fetch chapters directly
        try:
            chapters = fetch_json(f"{BASE}/api/chapter/by-book/{bid}")
            cnt = extract_section_pdfs(chapters, commission_dir)
            total += cnt
        except Exception as e:
            print(f"  Chapter fetch error: {e}")

print(f"\n\nTotal section PDFs downloaded: {total}")
