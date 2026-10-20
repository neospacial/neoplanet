"""Manifest: status, stale rule e, size budget, budget stop, warnings."""
import json
import os
import unittest

from helpers import REGISTRY, StoreCase, common, dataset
from lib import manifest


class ManifestTest(StoreCase):
    def test_budget_stop(self):
        self.assertFalse(manifest.budget_stop(300 * manifest.MB, 300))
        self.assertTrue(manifest.budget_stop(300 * manifest.MB + 1, 300))

    def test_deploy_stops_above_hard_stop(self):
        reg = {"datasets": [dataset("space.kp")], "budget_total_mb": 150, "hard_stop_mb": 300}
        self.process("space.kp")
        big = os.path.join(self.store.dir_for(dataset("space.kp")), "r", "big.json")
        with open(big, "wb") as f:
            f.truncate(301 * manifest.MB)      # sparse file: no real disk use
        man = manifest.build(self.store, reg, {}, {"space.kp": {"status": "ok"}}, self.now, "0.1.0")
        self.assertFalse(man["deploy"])
        self.assertTrue(any("hard stop" in w for w in man["warnings"]))
        self.assertTrue(any("2 x the budget" in w for w in man["warnings"]))

    def test_entry_fields_and_files(self):
        out = self.process("space.xray")
        reg = {"datasets": [dataset("space.xray")]}
        man = manifest.build(self.store, reg, {}, {"space.xray": out}, self.now, "0.1.0")
        e = man["datasets"]["space.xray"]
        self.assertEqual(e["status"], "ok")
        self.assertEqual(e["path"], "space/xray")
        self.assertEqual(e["files"]["r"], ["2026-10-20"])
        self.assertIn("latest", e["files"]["root"])
        self.assertEqual(len(e["hash"]), 16)
        self.assertGreater(e["bytes"], 0)

    def test_stale_uses_max_age_days(self):
        ds = dataset("ocean.sla")       # rule e: 45 days
        entry = {"status": "ok", "newest": self.now - 30 * 86400}
        self.assertEqual(manifest.status_for(entry, ds, self.now), "ok")
        entry["newest"] = self.now - 46 * 86400
        self.assertEqual(manifest.status_for(entry, ds, self.now), "stale")
        kp = dataset("space.kp")       # 1 day
        self.assertEqual(manifest.status_for({"status": "ok", "newest": self.now - 2 * 86400}, kp, self.now),
                         "stale")

    def test_error_and_degraded_stay(self):
        ds = dataset("space.kp")
        self.assertEqual(manifest.status_for({"status": "error", "newest": self.now}, ds, self.now), "error")
        self.assertEqual(manifest.status_for({"status": "degraded", "newest": self.now}, ds, self.now), "degraded")

    def test_previous_entry_is_kept_when_not_run(self):
        prev = {"datasets": {"space.kp": {"status": "ok", "newest": self.now - 3600, "last_ok": self.now - 3600}}}
        man = manifest.build(self.store, {"datasets": [dataset("space.kp")]}, prev, {}, self.now, "0.1.0")
        self.assertEqual(man["datasets"]["space.kp"]["status"], "ok")
        self.assertEqual(man["datasets"]["space.kp"]["newest"], self.now - 3600)

    def test_summary_markdown(self):
        man = manifest.build(self.store, REGISTRY, {}, {}, self.now, "0.1.0")
        md = manifest.summary_markdown(man, REGISTRY)
        self.assertIn("| space.kp |", md)
        self.assertIn("150 MB budget", md)


if __name__ == "__main__":
    unittest.main()
