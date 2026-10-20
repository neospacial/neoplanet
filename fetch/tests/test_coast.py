"""static/coast-110m.json: quantized Natural Earth coastlines from the fixture."""
import json
import os
import sys
import unittest

from helpers import FIXTURES, ROOT

sys.path.insert(0, os.path.join(ROOT, "tools"))
import make_coast  # noqa: E402


class CoastTest(unittest.TestCase):
    def test_file_matches_fixture(self):
        with open(os.path.join(FIXTURES, "static.ne-110m-coastline.json")) as f:
            want = make_coast.quantize(json.load(f))
        with open(os.path.join(ROOT, "static", "coast-110m.json")) as f:
            self.assertEqual(json.load(f), want)

    def test_round_trip(self):
        geo = {"features": [{"geometry": {"type": "LineString", "coordinates": [[-10.04, 50.0], [-9.5, 51.26]]}}]}
        q = make_coast.quantize(geo)
        line = q["lines"][0]
        self.assertEqual(line, [-100, 500, 5, 13])
        x, y = line[0] + line[2], line[1] + line[3]
        self.assertEqual((x / 10, y / 10), (-9.5, 51.3))


if __name__ == "__main__":
    unittest.main()
