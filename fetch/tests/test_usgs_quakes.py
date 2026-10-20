"""Adapter usgs_quakes: M2.5+ for 1 y, M4.5+ for 5 y, PAGER to sev."""
import unittest

from adapters.usgs import quake_sev
from helpers import StoreCase, common, dataset


class QuakesTest(StoreCase):
    def test_parse(self):
        items = self.parse("geo.quakes")["events"]["items"]
        self.assertEqual(len(items), 50)
        q = items[0]
        self.assertEqual((q["id"], q["mag"], q["lat"], q["lon"]), ("us6000u3nl", 5.4, 6.3226, -82.5693))
        self.assertEqual(q["extra"]["depth_km"], 10)
        self.assertEqual(q["sev"], 1)

    def test_sev(self):
        self.assertEqual(quake_sev(4.0, None), 0)
        self.assertEqual(quake_sev(6.5, "green"), 2)
        self.assertEqual(quake_sev(5.5, "red"), 4)        # PAGER wins

    def test_two_windows(self):
        ds = dataset("geo.quakes")
        old = self.now - 400 * 86400
        from lib import pipeline
        pipeline.write(ds, {"events": {"items": [
            {"id": "small", "t_start": old, "type": "quake", "mag": 3.0},
            {"id": "big", "t_start": old, "type": "quake", "mag": 5.1}]}, "newest": old}, self.ctx)
        ids = {e["id"] for e in self.store.all_events(ds)}
        self.assertEqual(ids, {"big"})


if __name__ == "__main__":
    unittest.main()
