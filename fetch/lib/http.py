"""HTTP client: conditional GET, User-Agent, backoff, hash change detection.

Plan 9.1 steps 2 to 4 and rule 9.4b. Standard library only.
"""
import gzip
import hashlib
import os
import threading
import time
import urllib.error
import urllib.parse
import urllib.request
import zlib
from collections import defaultdict

from . import common

TIMEOUT = 30            # seconds for each request (plan 9.2)
PER_HOST = 2            # max parallel requests to one host (plan 9.2)
BACKOFF = (5, 20, 60)   # wait before each retry after 429 or 5xx (plan 9.1 step 4)
MAX_BYTES = 120 * 1024 * 1024


class FetchError(Exception):
    """The request failed after all retries."""

    def __init__(self, message, status=0):
        super().__init__(message)
        self.status = status


class Response:
    def __init__(self, status, body=b"", headers=None, url=None, unchanged=False):
        self.status = status
        self.body = body
        self.headers = headers or {}
        self.url = url
        self.unchanged = unchanged   # True for 304 or for an equal SHA-256
        self.key = None              # masked URL, the key in the state
        self.validators = None       # saved by commit() after a good write

    def __repr__(self):
        return f"Response({self.status}, {len(self.body)} bytes, unchanged={self.unchanged})"


def sha256(data):
    return hashlib.sha256(data).hexdigest()


def _decode(raw, encoding):
    if "gzip" in (encoding or "").lower() or raw[:2] == b"\x1f\x8b":
        try:
            return gzip.decompress(raw)
        except (OSError, EOFError):
            return zlib.decompress(raw, 47)
    return raw


class HttpClient:
    """Network client. One instance for each run.

    state: dict URL -> {"etag", "last_modified", "sha256"}. The run saves it in
    data/_state/http.json. The keys of the dict are masked URLs.
    """

    def __init__(self, state=None, ua=None, sleep=time.sleep, opener=None, env=None, deadline=None):
        self.state = state if state is not None else {}
        self.deadline = deadline     # time.monotonic() value: no retry wait goes past it (plan 9.2)
        self.ua = ua or common.user_agent()
        self.sleep = sleep
        self.opener = opener or urllib.request.urlopen
        self.env = env
        self._lock = threading.Lock()
        self._sems = defaultdict(lambda: threading.Semaphore(PER_HOST))

    def _sem(self, url):
        host = urllib.parse.urlparse(url).netloc
        with self._lock:
            return self._sems[host]

    def _once(self, url, headers):
        req = urllib.request.Request(url, headers=headers)
        try:
            with self._sem(url):
                with self.opener(req, timeout=TIMEOUT) as r:
                    raw = r.read(MAX_BYTES)
                    hdrs = {k: v for k, v in r.headers.items()}
                    return Response(r.status, _decode(raw, hdrs.get("Content-Encoding")), hdrs, r.geturl())
        except urllib.error.HTTPError as e:
            hdrs = {k: v for k, v in (e.headers or {}).items()}
            return Response(e.code, b"", hdrs, url)

    def get(self, url, conditional=True, hash_check=False):
        """GET url. Follow redirects. Retry 429 and 5xx (plan 9.1 step 4).

        Return a Response. Raise FetchError on a final failure.
        """
        key = common.mask(url, self.env)
        with self._lock:
            st = dict(self.state.get(key) or {})
        headers = {"User-Agent": self.ua, "Accept-Encoding": "gzip", "Accept": "*/*"}
        if conditional:
            if st.get("etag"):
                headers["If-None-Match"] = st["etag"]
            if st.get("last_modified"):
                headers["If-Modified-Since"] = st["last_modified"]
        last_err = None
        conn_errors = 0
        for attempt in range(len(BACKOFF) + 1):
            if self.deadline is not None and time.monotonic() > self.deadline:
                raise last_err or FetchError("run time limit")
            try:
                r = self._once(url, headers)
            except Exception as e:   # DNS, TLS, timeout, connection reset
                last_err = FetchError(common.mask(f"{type(e).__name__}: {e}", self.env))
                r = None
                conn_errors += 1
                if conn_errors > 1:  # retry a connection error one time only
                    raise last_err
            if r is not None:
                if r.status == 304:
                    r.unchanged = True
                    return r
                if r.status == 200:
                    return self._accept(key, r, st, hash_check)
                if r.status != 429 and r.status < 500:
                    raise FetchError(f"HTTP {r.status}", r.status)
                last_err = FetchError(f"HTTP {r.status}", r.status)
            if attempt < len(BACKOFF):
                wait = BACKOFF[attempt]
                retry_after = r.headers.get("Retry-After") if r is not None else None
                if retry_after and retry_after.strip().isdigit():
                    wait = max(wait, min(int(retry_after), 120))
                if self.deadline is not None and time.monotonic() + wait > self.deadline:
                    raise last_err
                self.sleep(wait)
        raise last_err

    def _accept(self, key, r, old, hash_check):
        digest = sha256(r.body)
        new = {"etag": r.headers.get("ETag"), "last_modified": r.headers.get("Last-Modified"),
               "sha256": digest}
        has_validator = bool(new["etag"] or new["last_modified"])
        if (hash_check or not has_validator) and old.get("sha256") == digest:
            r.unchanged = True
        r.key = key
        r.validators = {k: v for k, v in new.items() if v}
        return r

    def commit(self, r):
        """Save the validators of a response. Call this only after the data is stored.

        If the parse or the write fails, the next run sends no validators and
        gets the full body again.
        """
        if r is not None and r.key and r.validators:
            with self._lock:
                self.state[r.key] = r.validators

    def forget(self, url):
        with self._lock:
            self.state.pop(common.mask(url, self.env), None)


class OfflineClient:
    """Read fixture files in place of the network (run.py --offline)."""

    def __init__(self, directory, fixtures=None):
        self.directory = directory
        self.fixtures = fixtures or {}   # URL -> fixture path
        self.state = {}

    def path_for(self, fixture):
        if not fixture:
            return None
        return os.path.join(self.directory, os.path.basename(fixture))

    def get(self, url, conditional=True, hash_check=False):
        fixture = self.fixtures.get(url)
        path = self.path_for(fixture)
        if not path or not os.path.exists(path):
            raise FetchError("no fixture for this URL (offline)", 404)
        with open(path, "rb") as f:
            return Response(200, f.read(), {}, url)

    def commit(self, r):
        pass

    def forget(self, url):
        pass
