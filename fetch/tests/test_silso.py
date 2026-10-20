"""Adapter silso_csv: daily sunspot number (full record) and the estimated number (class B)."""
import unittest

from helpers import StoreCase, common


class SilsoTest(StoreCase):
    def test_daily(self):
        s = self.parse("space.ssn-daily")["series"]
        self.assertEqual(s["rows"][common.parse_iso("2024-07-23")], [173.0, 17.5])
        self.assertEqual(s["rows"][common.parse_iso("1818-01-01")], [None, None])     # -1 is missing
        self.process("space.ssn-daily")
        shard = self.read("space.ssn-daily", "r/all.json")
        self.assertEqual(shard["dt"], 86400)          # regular daily record

    def test_estimated(self):
        s = self.parse("space.ssn-estimated")["series"]
        self.assertEqual(len(s["rows"]), 20)
        self.assertEqual(s["rows"][common.parse_iso("2026-10-20")], [71.0, 5.0])
        self.assertEqual(self.process("space.ssn-estimated")["status"], "ok")
        self.assertIsNotNone(self.read("space.ssn-estimated", "d1/all.json"))


if __name__ == "__main__":
    unittest.main()
