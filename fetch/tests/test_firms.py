"""Adapter firms: 1 degree cell counts (no points stored). The no-key file is a normal source (status ok)."""
import unittest

from helpers import StoreCase, dataset
from lib import grid as gridlib


class FirmsTest(StoreCase):
    def test_counts(self):
        r = self.parse("weather.fires")
        g = r["grid"]
        self.assertEqual(sum(g["values"]), 3000)
        self.assertEqual(g["values"][gridlib.cell_index(g["grid"], 39.89833, 28.87409)] >= 1, True)
        self.assertEqual(r["series"]["rows"][g["t"]], [3000])

    def test_no_key_is_ok_and_key_uses_alt_url(self):
        from lib import pipeline
        ds = dataset("weather.fires")
        url, fb = pipeline.primary_url(ds, self.ctx)
        self.assertFalse(fb)
        self.assertEqual(url, ds["url"])
        self.ctx.env = {"FIRMS_MAP_KEY": "k123"}
        url, fb = pipeline.primary_url(ds, self.ctx)
        self.assertFalse(fb)
        self.assertIn("/k123/", url)

    def test_store(self):
        out = self.process("weather.fires")
        self.assertEqual(out["status"], "ok")
        ds = dataset("weather.fires")
        self.assertEqual(len(self.store.grid_days(ds)), 1)
        self.assertEqual(len(self.store.list(ds, "w1")), 1)
        self.assertIsNotNone(self.read("weather.fires", "r/2026.json"))


if __name__ == "__main__":
    unittest.main()
