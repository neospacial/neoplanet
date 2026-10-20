"""Adapter gdacs: alert levels to sev."""
import unittest

from helpers import StoreCase


class GdacsTest(StoreCase):
    def test_parse(self):
        items = self.parse("geo.gdacs")["events"]["items"]
        self.assertEqual(len(items), 86)
        tc = next(e for e in items if e["id"] == "TC1001338")
        self.assertEqual((tc["sev"], tc["type"], tc["lat"], tc["lon"]), (4, "tc", 17.0, 133.0))
        self.assertEqual(tc["extra"]["level"], "Red")
        self.assertEqual({e["type"] for e in items}, {"eq", "tc", "fl", "vo", "dr", "wf"})

    def test_store(self):
        self.assertEqual(self.process("geo.gdacs")["status"], "ok")


if __name__ == "__main__":
    unittest.main()
