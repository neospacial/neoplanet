"""Adapter swpc_goes: X-ray, protons, electrons, magnetometer. Rule a (retry on parse error)."""
import json
import math
import unittest

from helpers import StoreCase, common, dataset, fixture_bytes


class SwpcGoesTest(StoreCase):
    def test_xray_two_channels(self):
        s = self.parse("space.xray")["series"]
        self.assertEqual([c["name"] for c in s["cols"]], ["short", "long"])
        self.assertEqual(len(s["rows"]), 300)
        last = s["rows"][max(s["rows"])]
        self.assertAlmostEqual(last[1], 5.152180051481992e-07)

    def test_xray_log_quantize(self):
        self.process("space.xray")
        shard = self.read("space.xray", "r/2026-10-20.json")
        self.assertEqual(shard["q"]["long"], {"type": "log10", "scale": 1000})
        v = [x for x in shard["cols"]["long"] if x is not None][-1]
        self.assertEqual(v, round(math.log10(5.152180051481992e-07) * 1000))

    def test_protons_kept_channels(self):
        s = self.parse("space.protons")["series"]
        self.assertEqual([c["name"] for c in s["cols"]], ["ge10", "ge50", "ge100"])
        self.assertEqual(len(s["rows"]), 75)

    def test_electrons(self):
        s = self.parse("space.electrons")["series"]
        self.assertEqual(len(s["rows"]), 287)
        self.assertEqual(s["dt"], 300)

    def test_magnetometer(self):
        s = self.parse("space.goes-mag")["series"]
        self.assertEqual([c["name"] for c in s["cols"]], ["He", "Hp", "Hn", "total"])
        self.assertEqual(len(s["rows"]), 600)

    def test_summary_tiers_written(self):
        self.process("space.xray")
        ds = dataset("space.xray")
        for tier in ("m5", "h1", "d1"):
            self.assertTrue(self.store.list(ds, tier), tier)
        m5 = self.read("space.xray", "m5/2026-10.json")
        self.assertEqual(sorted(m5["cols"])[:3], ["long.max", "long.mean", "long.min"])

    def test_truncated_body_retry(self):
        """Rule 9.4a: a truncated body is fetched again (online mode)."""
        good = fixture_bytes(dataset("space.protons"))
        bodies = [good[:5000], good[:9000], good]

        class Resp:
            def __init__(self, body):
                self.body, self.unchanged, self.status, self.key, self.validators = body, False, 200, None, None

        class Client:
            calls = 0

            def get(self, url, conditional=True, hash_check=False):
                Client.calls += 1
                return Resp(bodies[Client.calls - 1])

            def commit(self, r):
                pass

        self.ctx.client, self.ctx.offline = Client(), False
        out = self.process("space.protons")
        self.assertEqual(out["status"], "ok")
        self.assertEqual(Client.calls, 3)

    def test_truncated_body_gives_error_after_retries(self):
        bad = fixture_bytes(dataset("space.protons"))[:5000]

        class Client:
            def get(self, url, conditional=True, hash_check=False):
                from lib.http import Response
                return Response(200, bad)

            def commit(self, r):
                pass

        self.ctx.client, self.ctx.offline = Client(), False
        out = self.process("space.protons")
        self.assertEqual(out["status"], "error")
        self.assertIn("parse failed", out["message"])


if __name__ == "__main__":
    unittest.main()
