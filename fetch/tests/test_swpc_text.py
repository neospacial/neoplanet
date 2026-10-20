"""Adapter swpc_text: 3-day forecast, discussion, 27-day outlook (class F, 90 d)."""
import unittest

from helpers import StoreCase, common, dataset


class SwpcTextTest(StoreCase):
    def test_issue_times(self):
        self.assertEqual(common.iso(self.parse("space.3day-forecast")["text"]["t"]), "2026-10-20T12:30:00Z")
        self.assertEqual(common.iso(self.parse("space.discussion")["text"]["t"]), "2026-10-20T12:30:00Z")
        self.assertEqual(common.iso(self.parse("space.27day")["text"]["t"]), "2026-10-19T01:41:00Z")

    def test_store_and_prune(self):
        self.process("space.discussion")
        ds = dataset("space.discussion")
        self.assertEqual(self.store.list(ds, "r"), ["2026-10-20"])
        self.assertIn("Solar Activity", self.read("space.discussion", "latest.json")["issue"]["text"])
        self.clock.frozen = self.now + 91 * 86400
        self.store.prune_tier(ds, "r", "day", 90 * 86400)
        self.assertEqual(self.store.list(ds, "r"), [])

    def test_no_issue_line(self):
        from lib.validate import ParseError
        with self.assertRaises(ParseError):
            self.parse("space.discussion", b"no header here")


if __name__ == "__main__":
    unittest.main()
