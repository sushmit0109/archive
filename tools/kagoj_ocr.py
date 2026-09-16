# -*- coding: utf-8 -*-
"""Client for the kagoj.ai OCR service.

Flow, as used by the playground at https://kagoj.ai/playground/ocr:

    POST /api/ocr/upload            FormData: file, projectId?, deleteAfter?
    GET  /api/ocr/progress/{id}     -> status OCR_SUCCESS | COMPLETED
    GET  /api/ocr/download/{id}     -> text (outputFileType=txt)

All three need `Authorization: Bearer <token>`; the service is metered by
credits and caps a job at 50 pages, so long PDFs are split.

Credentials come from --auth-file or KAGOJ_TOKEN: either a bare access token
or the browser's `persist:auth` blob, which also carries the refresh token.
This never reads them from a browser profile itself.

State lives in a JSON ledger so an interrupted run resumes instead of
re-spending credits on chunks that already succeeded.
"""
import argparse, json, os, sys, time

# kagoj.ai only *records* finished jobs -- verified against a live account:
# POSTing a PDF there returns 201 but never processes it (page_count stays 0,
# no trigger route exists). The engine behind the playground is the Bangladesh
# Computer Council service below; the browser OCRs there, then posts the result
# to kagoj for billing at 20 credits/page.
LEDGER_BASE = "https://kagoj.ai"
OCR_BASE = "https://ocr.bangla.gov.bd/dev"
MAX_PAGES = 50           # the playground's own cap
POLL_SECONDS = 8         # matches the playground's polling interval
POLL_TIMEOUT = 600       # 10 minutes, as the playground uses


class Auth:
    """Bearer token, refreshed in place when the service says it expired.

    A full run is ~109 jobs and can take hours, comfortably outliving a short
    access token, so the refresh token is used to renew rather than failing
    the run partway through.
    """

    REFRESH_PATHS = ("/api/users/token/refresh/", "/api/users/token/refresh")

    def __init__(self, access, refresh=None):
        self.access = access
        self.refresh = refresh

    @classmethod
    def load(cls, args):
        """Accept a bare token, or the browser's `persist:auth` JSON blob."""
        raw = ""
        if args.auth_file:
            raw = open(args.auth_file).read().strip()
        elif os.environ.get("KAGOJ_TOKEN"):
            raw = os.environ["KAGOJ_TOKEN"].strip()
        if not raw:
            sys.exit("No credentials. Pass --auth-file or set KAGOJ_TOKEN.")
        if not raw.lstrip().startswith("{"):
            return cls(raw)
        blob = json.loads(raw)

        def unwrap(v):
            # redux-persist stores each field as a JSON-encoded string
            if isinstance(v, str) and v.startswith('"'):
                try:
                    return json.loads(v)
                except ValueError:
                    return v
            return v

        access = unwrap(blob.get("accessToken"))
        refresh = unwrap(blob.get("refreshToken"))
        if not access or access == "null":
            sys.exit("auth file has no accessToken")
        return cls(access, refresh if refresh not in (None, "null") else None)

    def headers(self):
        return {"Authorization": f"Bearer {self.access}", "Accept": "*/*"}

    def try_refresh(self, session):
        """Return True if a new access token was obtained."""
        if not self.refresh:
            return False
        for path in self.REFRESH_PATHS:
            for body in ({"refresh": self.refresh},
                         {"refreshToken": self.refresh}):
                try:
                    r = session.post(LEDGER_BASE + path, json=body, timeout=60)
                except Exception:
                    continue
                if r.status_code != 200:
                    continue
                try:
                    d = r.json()
                except ValueError:
                    continue
                tok = d.get("access") or d.get("accessToken") or d.get("token")
                if tok:
                    self.access = tok
                    if d.get("refresh") or d.get("refreshToken"):
                        self.refresh = d.get("refresh") or d.get("refreshToken")
                    return True
        return False


def split_pdf(path, outdir, max_pages=MAX_PAGES):
    """Split into <=max_pages chunks; returns [(chunk_path, first_page)]."""
    import fitz
    doc = fitz.open(path)
    os.makedirs(outdir, exist_ok=True)
    out = []
    for start in range(0, doc.page_count, max_pages):
        end = min(start + max_pages, doc.page_count) - 1
        chunk = fitz.open()
        chunk.insert_pdf(doc, from_page=start, to_page=end)
        p = os.path.join(outdir, f"{os.path.basename(path)}.{start:05d}.pdf")
        chunk.save(p)
        chunk.close()
        out.append((p, start))
    doc.close()
    return out


def ocr_chunk(session, auth, pdf_path, project_id=None, layout=1):
    """Upload one chunk to the OCR service, wait for it, return its text.

    It is not established that the kagoj token is the right credential for the
    OCR host, so the unauthenticated request is tried first and the token is
    only sent if the service actually demands one.
    """
    def upload(with_auth):
        with open(pdf_path, "rb") as fh:
            data = {"projectId": str(project_id)} if project_id else {}
            return session.post(
                f"{OCR_BASE}/api/ocr/upload",
                headers=auth.headers() if with_auth else {"Accept": "*/*"},
                files={"file": (os.path.basename(pdf_path), fh, "application/pdf")},
                data=data, timeout=240)

    r = upload(False)
    if r.status_code in (401, 403):
        r = upload(True)
        if r.status_code == 401 and auth.try_refresh(session):
            r = upload(True)
    if r.status_code in (401, 403):
        # Report what the server says it wants, so the required credential can
        # be identified rather than guessed at.
        hints = {k: v for k, v in r.headers.items()
                 if k.lower() in ("www-authenticate", "x-api-key", "server",
                                  "content-type", "allow")}
        raise PermissionError(
            f"{r.status_code} -- OCR host rejected anonymous and kagoj token.\n"
            f"        response headers: {hints}\n"
            f"        body: {r.text[:300]!r}")
    r.raise_for_status()
    body = r.json()
    job = body.get("id") or body.get("traceId") or body.get("trace_id")
    if not job:
        raise RuntimeError(f"upload returned no job id: {body}")

    deadline = time.time() + POLL_TIMEOUT
    while True:
        if time.time() > deadline:
            raise TimeoutError(f"job {job} still running after {POLL_TIMEOUT}s")
        time.sleep(POLL_SECONDS)
        pr = session.get(f"{OCR_BASE}/api/ocr/progress/{job}", headers=auth.headers(),
                         params={"projectId": project_id} if project_id else None,
                         timeout=60)
        if pr.status_code == 401:
            auth.try_refresh(session)
            continue
        if pr.status_code != 200:
            continue
        status = (pr.json() or {}).get("status", "")
        if status in ("OCR_SUCCESS", "COMPLETED"):
            break
        if "FAIL" in status.upper() or "ERROR" in status.upper():
            raise RuntimeError(f"job {job} failed: {status}")

    params = {"outputFileType": "txt", "layoutAlgorithm": layout}
    if project_id:
        params["projectId"] = project_id
    dr = session.get(f"{OCR_BASE}/api/ocr/download/{job}", headers=auth.headers(),
                     params=params, timeout=240)
    if dr.status_code == 401 and auth.try_refresh(session):
        dr = session.get(f"{OCR_BASE}/api/ocr/download/{job}", headers=auth.headers(),
                         params=params, timeout=240)
    dr.raise_for_status()
    try:
        j = dr.json()
        if isinstance(j, dict):
            for k in ("text", "content", "result", "data"):
                if isinstance(j.get(k), str):
                    return j[k]
            return json.dumps(j, ensure_ascii=False)
    except ValueError:
        pass
    return dr.text


def discover(session, auth):
    """Find the OCR service's real routes.

    The paths were inferred from the playground bundle and /api/ocr/upload
    404s, so ask the service itself: FastAPI/Flask services on this port
    usually publish a schema.
    """
    schema_paths = ["/openapi.json", "/docs", "/swagger.json", "/api/openapi.json",
                    "/redoc", "/api/docs", "/api-docs", "/"]
    print("--- schema endpoints ---")
    for p_ in schema_paths:
        try:
            r = session.get(OCR_BASE + p_, timeout=45)
            body = r.text[:200].replace("\n", " ")
            print(f"  GET {p_:<22} {r.status_code}  {body}")
            if r.status_code == 200 and p_.endswith(".json"):
                try:
                    spec = r.json()
                except ValueError:
                    spec = {}
                routes = spec.get("paths") or {}
                if routes:
                    print("\n  ROUTES IN SCHEMA:")
                    for route, ops in routes.items():
                        print(f"    {','.join(ops).upper():<12} {route}")
                    return
                print("  (schema published but paths are stripped)")
        except Exception as e:
            print(f"  GET {p_:<22} ERR {type(e).__name__}: {str(e)[:70]}")
    # FastAPI answers 404 only for routes it does not have; an existing route
    # replies 405 (wrong method) or 422 (missing/invalid body), and a 422 names
    # the fields it wanted. That makes method probing a reliable map.
    print("\n--- probing routes (404 = absent; 405/422 = exists) ---")
    cands = ["/api/ocr/upload", "/ocr/upload", "/upload", "/api/upload",
             "/ocr", "/api/ocr", "/api/v1/ocr/upload", "/v1/ocr/upload",
             "/api/ocr/file", "/api/ocr/process", "/api/ocr/ocr",
             "/process", "/api/process", "/predict", "/api/predict",
             "/ocr/process", "/ocr/predict", "/api/ocr/predict",
             "/extract", "/api/extract", "/ocr/extract", "/infer", "/api/infer"]
    found = []
    for p_ in cands:
        for method in ("POST", "GET"):
            try:
                r = session.request(method, OCR_BASE + p_, timeout=30)
            except Exception as e:
                print(f"  {method:<5}{p_:<22} ERR {str(e)[:50]}")
                continue
            if r.status_code != 404:
                print(f"  {method:<5}{p_:<22} {r.status_code}  {r.text[:260].strip()}")
                found.append((method, p_, r.status_code))
                break
    if not found:
        print("  (nothing but 404 -- the service may gate on a header or be "
              "reachable only through the gateway host)")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--discover", action="store_true",
                    help="probe the OCR service for its real routes")
    ap.add_argument("pdfs", nargs="*")
    ap.add_argument("--auth-file",
                    help="bare token, or the persist:auth JSON from the browser")
    ap.add_argument("--project-id")
    ap.add_argument("--layout", type=int, default=1)
    ap.add_argument("--ledger", default="ocr-ledger.json")
    ap.add_argument("--workdir", default="ocr-chunks")
    ap.add_argument("--probe", action="store_true",
                    help="OCR only the first chunk of the first PDF, then stop")
    args = ap.parse_args()

    from bangla_tls import ChainAdapter
    auth = Auth.load(args)
    # The OCR host serves a valid cert but omits the intermediate; this
    # completes the chain with verification left on.
    session = ChainAdapter.session("ocr.bangla.gov.bd", 443)

    if args.discover:
        discover(session, auth)
        return
    ledger = json.load(open(args.ledger)) if os.path.exists(args.ledger) else {}

    for pdf in args.pdfs:
        chunks = split_pdf(pdf, args.workdir)
        print(f"{os.path.basename(pdf)}: {len(chunks)} chunk(s)")
        for cpath, first in chunks:
            key = f"{os.path.basename(pdf)}#{first}"
            if key in ledger and ledger[key].get("text"):
                print(f"   [cached] {key}")
                continue
            t0 = time.time()
            try:
                text = ocr_chunk(session, auth, cpath, args.project_id, args.layout)
            except Exception as e:
                print(f"   [FAIL] {key}: {e}")
                ledger[key] = {"error": str(e)}
                json.dump(ledger, open(args.ledger, "w"), ensure_ascii=False)
                if isinstance(e, PermissionError):
                    sys.exit(1)
                continue
            ledger[key] = {"text": text, "seconds": round(time.time() - t0, 1)}
            json.dump(ledger, open(args.ledger, "w"), ensure_ascii=False)
            print(f"   [ok] {key}: {len(text):,} chars in {ledger[key]['seconds']}s")
            if args.probe:
                print("\n--- probe output (first 600 chars) ---")
                print(text[:600])
                return


if __name__ == "__main__":
    main()
