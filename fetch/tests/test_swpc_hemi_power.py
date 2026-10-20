"""Adapter swpc_hemi_power: hemispheric power text table."""
import unittest

from helpers import StoreCase, common


class SwpcHemiPowerTest(StoreCase):
    def test_parse(self):
        s = self.parse("space.hemi-power")["series"]
        self.assertEqual(len(s["rows"]), 215)
        self.assertEqual(s["rows"][common.parse_iso("2026-10-20T00:00:00Z")], [11.0, 11.0])
        self.assertEqual(s["rows"][max(s["rows"])], [40.0, 38.0])

    def test_store_class_b(self):
        self.assertEqual(self.process("space.hemi-power")["status"], "ok")
        self.assertIsNotNone(self.read("space.hemi-power", "r/2026-10-20.json"))
        self.assertIsNotNone(self.read("space.hemi-power", "d1/all.json"))


if __name__ == "__main__":
    unittest.main()
