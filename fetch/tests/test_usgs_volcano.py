"""Adapter usgs_volcano: elevated volcanoes. The source gives no coordinates."""
import unittest

from helpers import StoreCase


class VolcanoTest(StoreCase):
    def test_parse(self):
        items = self.parse("geo.volcanoes")["events"]["items"]
        self.assertEqual(len(items), 4)
        g = items[0]
        self.assertEqual(g["extra"]["volcano"], "Great Sitkin")
        self.assertEqual(g["sev"], 2)            # ORANGE
        self.assertEqual(g["title"], "Great Sitkin: Orange / Watch")
        self.assertNotIn("\\/", g["url"])


if __name__ == "__main__":
    unittest.main()
