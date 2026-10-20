"""Static checks of index.html (plan 11.1): one file, size, CSP, version, no external resources."""
import gzip
import os
import re
import unittest

from helpers import ROOT

CSP = ("default-src 'none'; script-src 'self' 'unsafe-inline'; style-src 'unsafe-inline'; "
       "connect-src 'self'; worker-src blob:; img-src 'none'")


class PageTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        with open(os.path.join(ROOT, "index.html"), "rb") as f:
            cls.raw = f.read()
        cls.html = cls.raw.decode("utf-8")

    def test_size(self):
        self.assertLess(len(self.raw), 120 * 1024)
        self.assertLess(len(gzip.compress(self.raw, 9)), 35 * 1024)

    def test_csp_exact(self):
        m = re.search(r'http-equiv="Content-Security-Policy" content="([^"]+)"', self.html)
        self.assertIsNotNone(m)
        self.assertEqual(m.group(1), CSP)

    def test_version_agrees(self):
        with open(os.path.join(ROOT, "VERSION")) as f:
            v = f.read().strip()
        self.assertIn(f'<meta name="version" content="{v}">', self.html)

    def test_no_external_resources(self):
        self.assertNotRegex(self.html, r'<(script|link|img|iframe)[^>]+(src|href)="(https?:)?//')
        self.assertNotIn("<img", self.html)
        self.assertNotIn("@import", self.html)
        self.assertNotIn("fonts.googleapis", self.html)
        # fetch() calls use relative paths only
        for m in re.finditer(r"fetch\(\s*'([^']+)'", self.html):
            self.assertFalse(m.group(1).startswith("http"), m.group(1))

    def test_disclaimer(self):
        self.assertIn("This dashboard is not an official warning service.", self.html)

    def test_static_files_are_small(self):
        d = os.path.join(ROOT, "static")
        if os.path.isdir(d):
            for f in os.listdir(d):
                self.assertLess(os.path.getsize(os.path.join(d, f)), 200 * 1024, f)


if __name__ == "__main__":
    unittest.main()
