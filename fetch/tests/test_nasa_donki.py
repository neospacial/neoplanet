"""Adapter nasa_donki: CME, FLR, GST, notifications.

No fixture exists: DONKI was rate limited in the audit. The fixture tests are
skipped until a fixture exists. Run audit.yml on the runner to get one
(artifact phase0-audit, folder samples/). The format tests use the field names
of the DONKI API documentation.
"""
import json
import os
import unittest

from helpers import FIXTURES, StoreCase, common, dataset


def fixture(name):
    p = os.path.join(FIXTURES, name)
    return open(p, "rb").read() if os.path.exists(p) else None


class DonkiFixtureTest(StoreCase):
    @unittest.skipUnless(fixture("nasa.donki-cme.json"), "skipped until a fixture exists")
    def test_cme_fixture(self):
        self.assertIn("events", self.parse("space.donki-cme", fixture("nasa.donki-cme.json")))

    @unittest.skipUnless(fixture("nasa.donki-flr.json"), "skipped until a fixture exists")
    def test_flr_fixture(self):
        self.assertIn("events", self.parse("space.donki-flr", fixture("nasa.donki-flr.json")))

    @unittest.skipUnless(fixture("nasa.donki-gst.json"), "skipped until a fixture exists")
    def test_gst_fixture(self):
        self.assertIn("events", self.parse("space.donki-gst", fixture("nasa.donki-gst.json")))

    @unittest.skipUnless(fixture("nasa.donki-notifications.json"), "skipped until a fixture exists")
    def test_notifications_fixture(self):
        self.assertIn("events", self.parse("space.donki-notifications", fixture("nasa.donki-notifications.json")))


class DonkiFormatTest(StoreCase):
    def test_cme(self):
        body = json.dumps([{"activityID": "2026-10-15T12:00:00-CME-001", "startTime": "2026-10-15T12:00Z",
                            "sourceLocation": "S15W30", "activeRegionNum": 4551, "link": "https://x/cme",
                            "cmeAnalyses": [{"speed": 650, "type": "C", "halfAngle": 30, "latitude": -10,
                                             "longitude": 20, "isMostAccurate": True}]}]).encode()
        e = self.parse("space.donki-cme", body)["events"]["items"][0]
        self.assertEqual((e["sev"], e["mag"], e["type"]), (1, 650, "cme"))
        self.assertEqual(e["t_start"], common.parse_iso("2026-10-15T12:00:00Z"))

    def test_flr(self):
        body = json.dumps([{"flrID": "F1", "beginTime": "2026-10-15T10:00Z", "peakTime": "2026-10-15T10:10Z",
                            "endTime": "2026-10-15T10:30Z", "classType": "X1.2"}]).encode()
        e = self.parse("space.donki-flr", body)["events"]["items"][0]
        self.assertEqual(e["sev"], 3)
        self.assertAlmostEqual(e["mag"], 1.2e-4)

    def test_gst(self):
        body = json.dumps([{"gstID": "G1", "startTime": "2026-10-15T03:00Z",
                            "allKpIndex": [{"observedTime": "2026-10-15T03:00Z", "kpIndex": 7.33}]}]).encode()
        e = self.parse("space.donki-gst", body)["events"]["items"][0]
        self.assertEqual((e["sev"], e["mag"]), (3, 7.33))

    def test_notification(self):
        body = json.dumps([{"messageType": "Report", "messageID": "M1", "messageURL": "https://x/m",
                            "messageIssueTime": "2026-10-15T12:00Z",
                            "messageBody": "## Message Type: Report\n\n## Summary:\n\nG2 storm observed.\n"}]).encode()
        e = self.parse("space.donki-notifications", body)["events"]["items"][0]
        self.assertEqual((e["title"], e["sev"], e["type"]), ("G2 storm observed.", 2, "report"))

    def test_empty_answer_is_valid(self):
        for body in (b"", b"[]"):
            self.assertEqual(self.parse("space.donki-cme", body)["events"]["items"], [])

    def test_demo_key_fallback_is_degraded(self):
        class Client:
            urls = []

            def get(self, url, conditional=True, hash_check=False):
                from lib.http import Response
                Client.urls.append(url)
                return Response(200, b"[]")

            def commit(self, r):
                pass

        self.ctx.client, self.ctx.offline = Client(), False
        out = self.process("space.donki-flr")
        self.assertEqual(out["status"], "degraded")
        self.assertIn("api_key=DEMO_KEY", Client.urls[0])
        self.ctx.env = {"NASA_API_KEY": "a-real-key-value"}
        out = self.process("space.donki-flr")
        self.assertEqual(out["status"], "ok")
        self.assertIn("api_key=a-real-key-value", Client.urls[1])


if __name__ == "__main__":
    unittest.main()
