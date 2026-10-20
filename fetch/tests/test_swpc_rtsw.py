"""Adapter swpc_rtsw: solar wind plasma and field. Rule c (active spacecraft only)."""
import json
import unittest

from helpers import StoreCase, dataset, fixture_bytes


class SwpcRtswTest(StoreCase):
    def test_only_active_rows(self):
        raw = json.loads(fixture_bytes(dataset("space.sw-plasma")))
        active = {r["time_tag"][:16] for r in raw if r["active"] is True}
        s = self.parse("space.sw-plasma")["series"]
        self.assertEqual(len(s["rows"]), len(active))
        self.assertEqual({v[-1] for v in s["rows"].values()}, {3})    # SOLAR1 code

    def test_plasma_columns(self):
        s = self.parse("space.sw-plasma")["series"]
        self.assertEqual([c["name"] for c in s["cols"]], ["speed", "density", "temperature", "src"])
        self.assertEqual(s["rows"][max(s["rows"])], [381.4, 6.78, 153579.0, 3])

    def test_mag_columns(self):
        s = self.parse("space.sw-mag")["series"]
        self.assertEqual([c["name"] for c in s["cols"]], ["bt", "bx", "by", "bz", "src"])
        self.assertEqual(s["rows"][max(s["rows"])], [6.72, -5.89, 2.07, -2.44, 3])

    def test_inactive_rows_dropped_when_rule_c(self):
        ds = dataset("space.sw-mag")
        raw = json.loads(fixture_bytes(ds))
        for r in raw:
            r["active"] = False
        from adapters import swpc
        from lib.validate import ParseError
        with self.assertRaises(ParseError):
            swpc.swpc_rtsw(ds, json.dumps(raw).encode(), self.ctx)

    def test_store(self):
        self.assertEqual(self.process("space.sw-mag")["status"], "ok")
        shard = self.read("space.sw-mag", "r/2026-10-20.json")
        self.assertEqual(shard["q"]["bz"], {"type": "lin", "scale": 10})
        self.assertEqual([v for v in shard["cols"]["bz"] if v is not None][-1], -24)


if __name__ == "__main__":
    unittest.main()
