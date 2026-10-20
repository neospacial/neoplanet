"""Adapter swpc_alerts: alerts, watches, warnings as events (1 year)."""
import unittest

from helpers import StoreCase, dataset


class SwpcAlertsTest(StoreCase):
    def test_parse(self):
        items = self.parse("space.alerts")["events"]["items"]
        self.assertEqual(len(items), 83)
        first = items[0]
        self.assertEqual(first["id"], "SUM10R-930")
        self.assertEqual(first["type"], "summary")
        watch = next(e for e in items if e["extra"]["code"] == "WATA20")
        self.assertEqual(watch["sev"], 1)        # G1 watch
        self.assertEqual(watch["type"], "watch")

    def test_merge_is_idempotent(self):
        self.process("space.alerts")
        ds = dataset("space.alerts")
        n1 = len(self.store.all_events(ds))
        self.process("space.alerts")
        self.assertEqual(len(self.store.all_events(ds)), n1)
        self.assertEqual(len(self.read("space.alerts", "active.json")["events"]), 83)


if __name__ == "__main__":
    unittest.main()
