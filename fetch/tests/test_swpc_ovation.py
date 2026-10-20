"""Adapter swpc_ovation: 2 degree aurora grid, max of the source cells, hourly snapshot, daily peak."""
import json
import unittest

from helpers import StoreCase, dataset, fixture_bytes, common
from lib import grid as gridlib


class SwpcOvationTest(StoreCase):
    def test_regrid_2deg_max(self):
        g = self.parse("space.aurora")["grid"]
        self.assertEqual(g["grid"], {"lat0": -89.0, "lon0": 1.0, "d": 2, "nlat": 90, "nlon": 180})
        self.assertEqual(len(g["values"]), 16200)
        self.assertEqual(sum(1 for v in g["values"] if v), 5415)    # plan 6.4 measured value
        src = json.loads(fixture_bytes(dataset("space.aurora")))["coordinates"]
        self.assertEqual(max(g["values"]), max(c[2] for c in src))
        # One cell by hand: lat [60, 62), lon [10, 12).
        want = max(c[2] for c in src if 60 <= c[1] < 62 and 10 <= c[0] < 12)
        k = gridlib.cell_index(g["grid"], 61, 11)
        self.assertEqual(g["values"][k], want)

    def test_store_snapshot_and_peak(self):
        self.assertEqual(self.process("space.aurora")["status"], "ok")
        ds = dataset("space.aurora")
        day = self.read("space.aurora", "2026-10-20.json")
        self.assertEqual(len(day["snaps"]), 1)
        self.assertEqual(day["enc"], "sparse-rle")
        self.assertEqual(self.store.list(ds, "d1"), ["2026-10-20"])
        latest = self.read("space.aurora", "latest.json")
        vals = gridlib.values_of(latest)
        self.assertEqual(sum(1 for v in vals if v), 5415)

    def test_one_snapshot_each_hour(self):
        ds = dataset("space.aurora")
        body = json.loads(fixture_bytes(ds))
        for minute, value in (("17:05", 50), ("17:43", 60), ("18:10", 70)):
            body["Observation Time"] = f"2026-10-20T{minute}:00Z"
            body["coordinates"][0][2] = value
            from adapters import swpc
            from lib import pipeline
            pipeline.write(ds, swpc.swpc_ovation(ds, json.dumps(body).encode(), self.ctx), self.ctx)
        day = self.read("space.aurora", "2026-10-20.json")
        self.assertEqual([common.iso(s["t"])[11:16] for s in day["snaps"]], ["17:43", "18:10"])
        peak = gridlib.values_of(self.read("space.aurora", "d1/2026-10-20.json"))
        self.assertEqual(peak[gridlib.cell_index(day["grid"], -90, 0)], 70)

    def test_truncated_grid_is_parse_error(self):
        from lib.validate import ParseError
        with self.assertRaises(ParseError):
            self.parse("space.aurora", fixture_bytes(dataset("space.aurora"))[:1000])


if __name__ == "__main__":
    unittest.main()
