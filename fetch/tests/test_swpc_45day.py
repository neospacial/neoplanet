"""Adapter swpc_45day: 45-day Ap and F10.7 forecast (latest only)."""
import unittest

from helpers import StoreCase, common


class Swpc45DayTest(StoreCase):
    def test_parse(self):
        f = self.parse("space.45day")["forecast"]
        self.assertEqual(len(f["rows"]), 45)
        self.assertEqual(f["rows"][common.parse_iso("2026-10-20")], [22.0, 120.0])
        self.assertEqual(common.iso(f["issued"]), "2026-10-20T00:00:00Z")

    def test_store(self):
        self.assertEqual(self.process("space.45day")["status"], "ok")
        self.assertEqual(self.read("space.45day", "latest.json")["series"]["n"], 45)


if __name__ == "__main__":
    unittest.main()
