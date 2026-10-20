"""HTTP client: conditional GET, 304, retry, Retry-After, hash change detection (rule b), commit."""
import email.message
import io
import unittest
import urllib.error

from helpers import common
from lib.http import FetchError, HttpClient


class FakeResp(io.BytesIO):
    def __init__(self, status, body, headers):
        super().__init__(body)
        self.status = status
        self.headers = email.message.Message()
        for k, v in headers.items():
            self.headers[k] = v
        self._url = "u"

    def geturl(self):
        return self._url

    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False


class Opener:
    def __init__(self, script):
        self.script = list(script)
        self.requests = []

    def __call__(self, req, timeout=None):
        self.requests.append(dict(req.header_items()))
        status, body, headers = self.script.pop(0)
        if status >= 400 or status == 304:
            msg = email.message.Message()
            for k, v in headers.items():
                msg[k] = v
            raise urllib.error.HTTPError("u", status, "x", msg, io.BytesIO(b""))
        return FakeResp(status, body, headers)


class HttpTest(unittest.TestCase):
    def client(self, script, state=None, env=None):
        self.sleeps = []
        op = Opener(script)
        return HttpClient(state if state is not None else {}, ua="ua-test", sleep=self.sleeps.append,
                          opener=op, env=env or {}), op

    def test_conditional_headers_and_304(self):
        c, op = self.client([(200, b"a", {"ETag": '"e1"'}), (304, b"", {})])
        r = c.get("http://h/x")
        self.assertFalse(r.unchanged)
        c.commit(r)
        r2 = c.get("http://h/x")
        self.assertTrue(r2.unchanged)
        self.assertEqual(op.requests[1].get("If-none-match"), '"e1"')
        self.assertEqual(op.requests[0]["User-agent"], "ua-test")

    def test_validators_saved_only_on_commit(self):
        c, op = self.client([(200, b"a", {"ETag": '"e1"'}), (200, b"a", {"ETag": '"e1"'})])
        c.get("http://h/x")          # parse failed: no commit
        c.get("http://h/x")
        self.assertNotIn("If-none-match", op.requests[1])

    def test_retry_5xx_and_retry_after(self):
        c, op = self.client([(503, b"", {}), (429, b"", {"Retry-After": "30"}), (200, b"ok", {})])
        r = c.get("http://h/x")
        self.assertEqual(r.body, b"ok")
        self.assertEqual(self.sleeps, [5, 30])

    def test_gives_up(self):
        c, op = self.client([(500, b"", {})] * 4)
        with self.assertRaises(FetchError):
            c.get("http://h/x")
        self.assertEqual(self.sleeps, [5, 20, 60])

    def test_404_no_retry(self):
        c, op = self.client([(404, b"", {})])
        with self.assertRaises(FetchError) as e:
            c.get("http://h/x")
        self.assertEqual(e.exception.status, 404)
        self.assertEqual(self.sleeps, [])

    def test_hash_change_detection(self):
        c, op = self.client([(200, b"same", {}), (200, b"same", {}), (200, b"new", {})])
        c.commit(c.get("http://h/x", hash_check=True))
        self.assertTrue(c.get("http://h/x", hash_check=True).unchanged)
        self.assertFalse(c.get("http://h/x", hash_check=True).unchanged)

    def test_state_keys_are_masked(self):
        env = {"NASA_API_KEY": "SECRETKEY99"}
        c, op = self.client([(200, b"a", {"ETag": "x"})], env=env)
        c.commit(c.get("http://h/x?api_key=SECRETKEY99"))
        self.assertEqual(list(c.state), ["http://h/x?api_key=***"])

    def test_connection_error_retries_once(self):
        calls = []

        def opener(req, timeout=None):
            calls.append(1)
            raise ConnectionResetError("reset")

        c = HttpClient({}, ua="x", sleep=lambda s: None, opener=opener)
        with self.assertRaises(FetchError):
            c.get("http://h/x")
        self.assertEqual(len(calls), 2)

    def test_deadline_stops_retries(self):
        import time
        c, op = self.client([(503, b"", {})] * 4)
        c.deadline = time.monotonic() + 10       # the 20 s wait would pass the deadline
        with self.assertRaises(FetchError):
            c.get("http://h/x")
        self.assertEqual(self.sleeps, [5])

    def test_gzip(self):
        import gzip
        c, op = self.client([(200, gzip.compress(b"hello"), {"Content-Encoding": "gzip"})])
        self.assertEqual(c.get("http://h/x").body, b"hello")


if __name__ == "__main__":
    unittest.main()
