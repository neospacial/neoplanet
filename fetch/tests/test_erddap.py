"""Adapter erddap_grid: SST and sea level anomaly grids, derived scalars, coral alert (no fixture)."""
import os
import unittest

from helpers import FIXTURES, StoreCase, common, dataset
from lib import grid as gridlib


class ErddapTest(StoreCase):
    def test_sst(self):
        r = self.parse("ocean.sst-anom")
        g = r["grid"]
        self.assertEqual(g["grid"], {"lat0": -89.5, "lon0": -179.5, "d": 1, "nlat": 180, "nlon": 360})
        self.assertEqual(common.iso(g["t"]), "2026-10-19T12:00:00Z")
        k = gridlib.cell_index(g["grid"], 88.125, 358.125 - 360)
        self.assertEqual(g["values"][k], 0.11)
        self.assertIsNone(g["values"][gridlib.cell_index(g["grid"], -89.875, 0.125)])     # NaN is land or ice
        mean, nino = r["series"]["rows"][common.parse_iso("2026-10-19")]
        self.assertAlmostEqual(nino, 3.4, delta=0.3)      # CPC weekly Nino 3.4 anomaly is 3.3
        self.assertTrue(-1 < mean < 2)

    def test_sla_global_mean(self):
        r = self.parse("ocean.sla")
        self.assertEqual([c["name"] for c in r["series"]["cols"]], ["global_mean"])
        self.assertEqual(common.iso(r["grid"]["t"]), "2026-09-28T00:00:00Z")

    def test_store_and_week(self):
        self.assertEqual(self.process("ocean.sst-anom")["status"], "ok")
        ds = dataset("ocean.sst-anom")
        self.assertEqual(self.store.grid_days(ds), ["2026-10-19"])
        self.assertEqual(self.store.list(ds, "w1"), ["2026-10-19"])     # Monday of the week
        latest = self.read("ocean.sst-anom", "latest.json")
        vals = gridlib.values_of(latest)
        self.assertEqual(sum(v is not None for v in vals), sum(v is not None for v in self.parse("ocean.sst-anom")["grid"]["values"]))

    def test_area_mean_box(self):
        g = gridlib.spec(10)
        vals = [1.0] * (g["nlat"] * g["nlon"])
        self.assertAlmostEqual(gridlib.area_mean(vals, g), 1.0)
        k = gridlib.cell_index(g, 0, -150)
        vals[k] = 5.0
        self.assertAlmostEqual(gridlib.area_mean(vals, g, (1, 9, -149, -141)), 5.0)      # one cell: center (5, -145)

    @unittest.skipUnless(os.path.exists(os.path.join(FIXTURES, "erddap.coral-alert.csv")), "skipped until a fixture exists")
    def test_coral_fixture(self):
        with open(os.path.join(FIXTURES, "erddap.coral-alert.csv"), "rb") as f:
            self.assertIn("grid", self.parse("ocean.coral-alert", f.read()))

    def test_coral_format(self):
        body = ("time,latitude,longitude,CRW_BAA_7D_MAX\nUTC,degrees_north,degrees_east,1\n"
                "2026-10-19T12:00:00Z,89.975,-179.975,NaN\n2026-10-19T12:00:00Z,-10.025,150.025,3\n").encode()
        g = self.parse("ocean.coral-alert", body)["grid"]
        self.assertEqual(g["grid"]["d"], 2)
        self.assertEqual(g["values"][gridlib.cell_index(g["grid"], -10.025, 150.025)], 3)


if __name__ == "__main__":
    unittest.main()
