"""Adapters nhc_storms (rule g: empty list) and ibtracs (tracks)."""
import json
import unittest

from adapters.storms import saffir
from helpers import StoreCase


class StormsTest(StoreCase):
    def test_nhc_empty(self):
        self.assertEqual(self.parse("weather.nhc")["events"]["items"], [])
        self.assertEqual(self.process("weather.nhc")["status"], "ok")

    def test_nhc_storm(self):
        body = json.dumps({"activeStorms": [{"id": "al052026", "name": "Ernesto", "classification": "HU",
                                             "intensity": "100", "pressure": "960", "latitudeNumeric": 25.1,
                                             "longitudeNumeric": -70.2, "lastUpdate": "2026-10-20T15:00:00.000Z"}]})
        e = self.parse("weather.nhc", body.encode())["events"]["items"][0]
        self.assertEqual((e["sev"], e["mag"], e["title"]), (3, 100, "HU Ernesto"))

    def test_saffir(self):
        self.assertEqual([saffir(k) for k in (None, 50, 64, 83, 96, 113, 137)], [0, 0, 1, 2, 3, 4, 5])

    def test_ibtracs(self):
        items = self.parse("weather.ibtracs")["events"]["items"]
        self.assertEqual(len(items), 6)
        w = next(e for e in items if e["id"] == "2026289S11197")
        self.assertEqual(w["title"], "Wati (SP)")
        self.assertGreater(len(w["extra"]["track"]), 3)
        self.assertEqual(w["extra"]["track"][0][0], 0)


if __name__ == "__main__":
    unittest.main()
