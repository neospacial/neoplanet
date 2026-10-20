"""Key masking, URL placeholders, durations, time helpers."""
import os
import unittest

from helpers import StoreCase, common


class MaskTest(unittest.TestCase):
    def test_mask_values(self):
        env = {"NASA_API_KEY": "abc123secretvalue", "FIRMS_MAP_KEY": "f1rmsk3y"}
        s = "https://api.nasa.gov/x?api_key=abc123secretvalue and f1rmsk3y"
        self.assertEqual(common.mask(s, env), "https://api.nasa.gov/x?api_key=*** and ***")

    def test_demo_key_is_not_masked(self):
        self.assertEqual(common.mask("api_key=DEMO_KEY", {}), "api_key=DEMO_KEY")

    def test_written_file_is_masked(self):
        import tempfile
        env = {"NASA_API_KEY": "zz-secret-zz"}
        d = tempfile.mkdtemp()
        p = os.path.join(d, "a.json")
        common.write_json(p, {"url": "https://x/?api_key=zz-secret-zz"}, env)
        with open(p) as f:
            self.assertNotIn("zz-secret-zz", f.read())


class ExpandTest(unittest.TestCase):
    now = common.parse_iso("2026-10-20T18:00:00Z")

    def test_dates(self):
        url, fb = common.expand_url("x?s={D-30}&e={D0}&w={D-7}&y={Y}", self.now, {})
        self.assertEqual(url, "x?s=2026-09-20&e=2026-10-20&w=2026-10-13&y=2026")
        self.assertFalse(fb)

    def test_nasa_fallback(self):
        url, fb = common.expand_url("x?api_key={NASA_API_KEY}", self.now, {})
        self.assertEqual(url, "x?api_key=DEMO_KEY")
        self.assertTrue(fb)
        url, fb = common.expand_url("x?api_key={NASA_API_KEY}", self.now, {"NASA_API_KEY": "k"})
        self.assertEqual(url, "x?api_key=k")
        self.assertFalse(fb)

    def test_extra(self):
        url, _ = common.expand_url("id={OBS}", self.now, {}, {"OBS": "BOU"})
        self.assertEqual(url, "id=BOU")


class TimeTest(unittest.TestCase):
    def test_duration(self):
        self.assertEqual(common.duration("7d"), 7 * 86400)
        self.assertEqual(common.duration("1y"), 365 * 86400)
        self.assertEqual(common.duration("30m"), 1800)
        self.assertIsNone(common.duration(True))
        self.assertIsNone(common.duration("full"))

    def test_parse_iso(self):
        self.assertEqual(common.parse_iso("2026-10-20T00:00:00Z"), common.parse_iso("2026-10-20 00:00:00"))
        self.assertEqual(common.parse_iso("2026-10-20"), common.epoch(2026, 10, 20))
        self.assertEqual(common.iso(common.week_start(common.parse_iso("2026-10-22T10:00:00Z"))),
                         "2026-10-19T00:00:00Z")

    def test_user_agent_has_no_email(self):
        ua = common.user_agent()
        self.assertTrue(ua.startswith("public-data-dashboard/"))
        self.assertNotIn("@", ua)


if __name__ == "__main__":
    unittest.main()
