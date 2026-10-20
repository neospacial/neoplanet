"""Adapter usgs_geomag: three observatories, H, D, Z, 1 minute."""
import unittest

from adapters import usgs
from helpers import StoreCase, common, dataset, fixture_bytes
from lib import store as st


class GeomagTest(StoreCase):
    def test_parse(self):
        rows = usgs.parse_geomag(fixture_bytes(dataset("space.geomag")))
        t0 = common.parse_iso("2026-10-20T00:00:00Z")
        self.assertAlmostEqual(rows[t0]["H"], 20670.923)
        import json
        raw = json.loads(fixture_bytes(dataset("space.geomag")))
        h = next(v for v in raw["values"] if v["id"] == "H")["values"]
        self.assertEqual(len(rows), sum(1 for x in h if x is not None))   # null rows at the end are skipped

    def test_offline_first_observatory(self):
        out = self.process("space.geomag")
        self.assertEqual(out["status"], "ok")
        self.assertIn("FRD", out["message"])
        shard = self.read("space.geomag", "r/2026-10-20.json")
        self.assertEqual(shard["q"]["BOU_H"]["off"], 20700)       # per-shard offset
        self.assertNotIn("HON_H", [k for k, v in shard["cols"].items() if any(x is not None for x in v)])
        rows = st.decode_series(shard, ["BOU_H"])
        self.assertAlmostEqual(rows[common.parse_iso("2026-10-20T00:00:00Z")][0], 20671, delta=0.5)

    def test_d_has_no_summary(self):
        self.process("space.geomag")
        m5 = self.read("space.geomag", "m5/2026-10.json")
        self.assertIn("BOU_H.max", m5["cols"])
        self.assertNotIn("BOU_D.max", m5["cols"])

    def test_all_observatories_fail(self):
        from lib.http import FetchError

        class Client:
            def get(self, *a, **k):
                raise FetchError("HTTP 503", 503)

        self.ctx.client, self.ctx.offline = Client(), False
        out = self.process("space.geomag")
        self.assertEqual(out["status"], "error")

    def test_window_parameters_online(self):
        urls = []

        class Client:
            def get(self, url, conditional=True, hash_check=False):
                from lib.http import Response
                urls.append(url)
                return Response(200, fixture_bytes(dataset("space.geomag")))

            def commit(self, r):
                pass

        self.ctx.client, self.ctx.offline = Client(), False
        self.process("space.geomag")
        self.assertEqual(len(urls), 3)
        self.assertIn("id=HON", urls[2])
        self.assertIn("starttime=2026-10-20T14:00:00Z", urls[0])


if __name__ == "__main__":
    unittest.main()
