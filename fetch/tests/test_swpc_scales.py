"""Adapter swpc_scales: NOAA R/S/G now, 24 h maximum, forecast."""
import unittest

from helpers import StoreCase


class SwpcScalesTest(StoreCase):
    def test_record(self):
        r = self.parse("space.scales")["record"]
        self.assertEqual((r["now"]["R"], r["now"]["S"], r["now"]["G"]), (0, 0, 0))
        self.assertEqual(len(r["forecast"]), 3)
        self.assertEqual(r["forecast"][0]["G"], 1)
        self.assertEqual(r["forecast"][0]["R_minor_prob"], 25)

    def test_series_history(self):
        self.process("space.scales")
        latest = self.read("space.scales", "latest.json")
        self.assertEqual(latest["record"]["max24"]["date"], "2026-10-19")
        shard = self.read("space.scales", "r/2026.json")
        self.assertEqual(shard["cols"]["g"], [0])


if __name__ == "__main__":
    unittest.main()
