"""Adapters jpl_cad, jpl_fireball, jpl_sentry. Rule b (hash change detection)."""
import unittest

from adapters.jpl import AU_LD, diameter_from_h
from helpers import StoreCase, common, dataset


class JplTest(StoreCase):
    def test_cad(self):
        items = self.parse("space.neo-cad")["events"]["items"]
        self.assertEqual(len(items), 40)
        first = items[0]
        self.assertEqual(first["extra"]["des"], "2026 TD2")
        self.assertAlmostEqual(first["mag"], 0.0186216759072865 * AU_LD, places=2)
        self.assertEqual(common.iso(first["t_start"]), "2026-10-20T05:06:00Z")

    def test_cad_window_prune(self):
        ds = dataset("space.neo-cad")
        self.process("space.neo-cad")
        n = len(self.store.all_events(ds))
        self.clock.frozen = self.now + 40 * 86400          # 40 d later: the first approaches leave the window
        from lib import pipeline
        self.store.merge_events(ds, [], pipeline.event_keep(ds))
        self.assertLess(len(self.store.all_events(ds)), n)

    def test_fireball(self):
        items = self.parse("space.fireballs")["events"]["items"]
        self.assertEqual(len(items), 1074)
        f = items[0]
        self.assertEqual(f["id"], "2026-10-04 03:14:45")
        self.assertEqual((f["lat"], f["lon"]), (-41.8, -173.1))      # S and W are negative
        self.assertEqual(f["mag"], 0.18)
        self.assertEqual(self.process("space.fireballs")["status"], "ok")
        self.assertIn("2026", self.store.event_keys(dataset("space.fireballs")))   # yearly files (full record)

    def test_sentry(self):
        rec = self.parse("space.sentry")["record"]
        self.assertEqual(rec["count"], 600)
        ps = [o["ps_cum"] for o in rec["objects"]]
        self.assertEqual(ps, sorted(ps, reverse=True))

    def test_hash_rule_b(self):
        self.assertIn("b", dataset("space.sentry")["rules"])

    def test_diameter(self):
        self.assertAlmostEqual(diameter_from_h(22.0), 140, delta=5)


if __name__ == "__main__":
    unittest.main()
