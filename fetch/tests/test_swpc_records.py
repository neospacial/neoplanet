"""Adapter swpc_records: estimated Kp, Enlil, flare probabilities, regions, solar cycle."""
import unittest

from helpers import StoreCase, common


class SwpcRecordsTest(StoreCase):
    def test_kp_1m(self):
        s = self.parse("space.kp-1m")["series"]
        self.assertEqual(len(s["rows"]), 358)
        self.assertEqual(s["dt"], 60)
        self.assertEqual(self.process("space.kp-1m")["status"], "ok")
        self.assertIn("2026-10-20", self.store.list({"id": "space.kp-1m", "kind": "series"}, "r"))

    def test_enlil_forecast(self):
        f = self.parse("space.enlil")["forecast"]
        self.assertEqual(len(f["rows"]), 600)
        self.assertGreater(max(f["rows"]), self.now)    # rule f: future times are normal
        self.assertEqual(self.process("space.enlil")["status"], "ok")

    def test_flare_probabilities_newest_row(self):
        r = self.parse("space.flare-prob")["record"]
        self.assertEqual(common.iso(r["t"]), "2026-10-20T00:00:00Z")
        self.assertEqual(r["values"]["m_class_1_day"], 25)

    def test_solar_regions_one_event_per_region(self):
        items = self.parse("space.solar-regions")["events"]["items"]
        ids = [e["id"] for e in items]
        self.assertEqual(len(ids), len(set(ids)))
        self.assertEqual(len(items), 31)
        ar = next(e for e in items if e["id"] == "AR4556")
        self.assertEqual(ar["title"], "Region 4556 N03W41")
        self.assertIsNone(ar["lat"])     # heliographic position stays in 'extra'
        self.assertEqual(ar["extra"]["latitude"], 3)

    def test_cycle_observed_full_record(self):
        s = self.parse("space.cycle-observed")["series"]
        self.assertEqual(len(s["rows"]), 600)
        last = s["rows"][common.epoch(2026, 9)]
        self.assertEqual(last[0], 60.3)
        self.assertIsNone(last[1])          # -1 is a fill value
        self.process("space.cycle-observed")
        shard = self.read("space.cycle-observed", "r/all.json")
        self.assertIn("t", shard)           # irregular: monthly times

    def test_cycle_predicted(self):
        f = self.parse("space.cycle-predicted")["forecast"]
        self.assertEqual(len(f["rows"]), 57)
        self.assertEqual([c["name"] for c in f["cols"]][:3], ["predicted_ssn", "low_ssn", "high_ssn"])


if __name__ == "__main__":
    unittest.main()
