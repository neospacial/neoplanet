"""Adapter ndbc_dart: rule d (station list, skip 404 and stale stations)."""
import unittest

from adapters import ndbc
from helpers import StoreCase, common, dataset, fixture_bytes
from lib.http import FetchError, Response


class DartTest(StoreCase):
    def test_station_list(self):
        st = ndbc.stations(fixture_bytes(dataset("geo.dart")["station_list_fixture"]))
        self.assertEqual(len(st), 76)
        self.assertEqual(st[0]["id"], "21413")

    def test_parse_rows(self):
        rows = ndbc.parse_dart(fixture_bytes(dataset("geo.dart")).decode())
        self.assertEqual(rows[common.parse_iso("2026-07-30T02:14:00Z")], 5421.348)

    def test_stale_station_is_skipped(self):
        out = self.process("geo.dart")      # the fixture station is 40 days old
        self.assertEqual(out["status"], "error")
        import json, os
        st = json.load(open(os.path.join(self.tmp, "_state", "dart.json")))
        self.assertEqual(st["skip"]["21414"], "stale")

    def test_fresh_station(self):
        text = fixture_bytes(dataset("geo.dart")).decode()
        # Move the data to the last day: the station is then fresh.
        shift = self.now - common.parse_iso("2026-07-30T03:00:00Z")
        lines = []
        for line in text.splitlines():
            m = ndbc._ROW.match(line)
            if m:
                t = common.epoch(*[int(x) for x in m.groups()[:6]]) + shift
                d = common.utc(t)
                line = f"{d:%Y %m %d %H %M %S} {m.group(7)} {m.group(8)}"
            lines.append(line)
        body = "\n".join(lines).encode()
        xml = fixture_bytes(dataset("geo.dart")["station_list_fixture"])

        class Client:
            def get(self, url, conditional=True, hash_check=False):
                if url.endswith("activestations.xml"):
                    return Response(200, xml)
                if "/21414.dart" in url:
                    return Response(200, body)
                raise FetchError("HTTP 404", 404)

            def commit(self, r):
                pass

        self.ctx.client, self.ctx.offline = Client(), False
        out = self.process("geo.dart")
        self.assertEqual(out["status"], "ok")
        self.assertIn("1 fresh stations", out["message"])
        latest = self.read("geo.dart", "latest.json")
        self.assertEqual(latest["record"]["stations"][0]["id"], "21414")
        self.assertIn("h_21414", latest["last"])


if __name__ == "__main__":
    unittest.main()
