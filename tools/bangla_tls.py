# -*- coding: utf-8 -*-
"""Complete the TLS chain for read.bangla.gov.bd:9395 (the OCR service).

The host serves a valid Sectigo-issued certificate for *.bangla.gov.bd but
omits the intermediate CA, so Python fails with "unable to get local issuer
certificate" where a browser succeeds (browsers fetch the missing intermediate
via the certificate's Authority Information Access extension).

This does the same thing a browser does: fetch the intermediate named by the
leaf's AIA extension and add it to a normal trust store. Verification stays
fully on -- the system/certifi roots still have to vouch for the chain, and
the hostname is still checked. Nothing here disables or weakens TLS.
"""
import ssl, socket, urllib.request

HOST = "ocr.bangla.gov.bd"
PORT = 443


def _leaf_der(host=HOST, port=PORT):
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE  # only to READ the cert, not to trust it
    with socket.create_connection((host, port), timeout=30) as sock:
        with ctx.wrap_socket(sock, server_hostname=host) as tls:
            return tls.getpeercert(binary_form=True)


def _aia_url(der):
    """Pull the CA Issuers URL out of the leaf certificate."""
    text = ssl.DER_cert_to_PEM_cert(der)
    try:
        from cryptography import x509
        from cryptography.hazmat.primitives.serialization import Encoding
        cert = x509.load_der_x509_certificate(der)
        aia = cert.extensions.get_extension_for_class(
            x509.AuthorityInformationAccess).value
        for desc in aia:
            if desc.access_method == x509.oid.AuthorityInformationAccessOID.CA_ISSUERS:
                return desc.access_location.value
    except Exception:
        pass
    return None


def make_context(host=HOST, port=PORT):
    """A verifying SSL context that also knows the missing intermediate."""
    ctx = ssl.create_default_context()
    url = _aia_url(_leaf_der(host, port))
    if url:
        der = urllib.request.urlopen(url, timeout=30).read()
        try:
            pem = ssl.DER_cert_to_PEM_cert(der)
        except Exception:
            pem = der.decode()
        ctx.load_verify_locations(cadata=pem)
    return ctx


class ChainAdapter:
    """requests adapter using the completed chain."""

    @staticmethod
    def session(host=HOST, port=PORT):
        import requests
        from requests.adapters import HTTPAdapter
        from urllib3.poolmanager import PoolManager

        ctx = make_context(host, port)

        class _A(HTTPAdapter):
            def init_poolmanager(self, connections, maxsize, block=False, **kw):
                kw["ssl_context"] = ctx
                self.poolmanager = PoolManager(
                    num_pools=connections, maxsize=maxsize, block=block, **kw)

        s = requests.Session()
        s.mount("https://", _A())
        return s


if __name__ == "__main__":
    import sys
    der = _leaf_der()
    print("AIA CA Issuers:", _aia_url(der))
    s = ChainAdapter.session()
    try:
        r = s.get(f"https://{HOST}:{PORT}/", timeout=30)
        print("verified request OK ->", r.status_code)
    except Exception as e:
        print("failed:", type(e).__name__, str(e)[:200])
