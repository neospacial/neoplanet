"""Adapter swpc_flares: GOES flare list with the NOAA R level."""
import unittest

from adapters.swpc import flare_r
from helpers import StoreCase


class SwpcFlaresTest(StoreCase):
    def test_parse(self):
        items = self.parse("space.xray-flares")["events"]["items"]
        self.assertEqual(len(items), 79)
        self.assertEqual(items[0]["title"], "B9.9 flare")
        self.assertTrue(all(e["type"] == "flare" for e in items))

    def test_r_scale(self):
        self.assertEqual(flare_r(9e-6), 0)
        self.assertEqual(flare_r(1e-5), 1)     # M1
        self.assertEqual(flare_r(5e-5), 2)     # M5
        self.assertEqual(flare_r(1e-4), 3)     # X1
        self.assertEqual(flare_r(1e-3), 4)     # X10
        self.assertEqual(flare_r(2e-3), 5)     # X20

    def test_store(self):
        self.assertEqual(self.process("space.xray-flares")["status"], "ok")
        self.assertIsNotNone(self.read("space.xray-flares", "2026-10.json"))


if __name__ == "__main__":
    unittest.main()
