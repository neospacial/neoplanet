"""Adapter nasa_eonet: the newest geometry point gives the position."""
import unittest

from adapters.nasa import _point
from helpers import StoreCase, common


class EonetTest(StoreCase):
    def test_parse(self):
        items = self.parse("geo.eonet")["events"]["items"]
        self.assertEqual(len(items), 52)
        e = next(x for x in items if x["id"] == "EONET_25457")
        self.assertEqual((e["lat"], e["lon"], e["type"], e["mag"]), (-4.5, 53.8, "severeStorms", 35.0))
        self.assertEqual(e["extra"]["unit"], "kts")

    def test_polygon_centroid(self):
        self.assertEqual(_point({"type": "Polygon", "coordinates": [[[0, 0], [2, 0], [2, 2], [0, 2]]]}), (1, 1))


if __name__ == "__main__":
    unittest.main()
