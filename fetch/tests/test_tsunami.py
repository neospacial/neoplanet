"""Adapter tsunami_atom: NTWC and PTWC Atom feeds. Rule g: an empty feed is valid."""
import unittest

from helpers import StoreCase, common


class TsunamiTest(StoreCase):
    def test_ntwc(self):
        items = self.parse("geo.tsunami-ntwc")["events"]["items"]
        self.assertEqual(len(items), 1)
        e = items[0]
        self.assertEqual((e["lat"], e["lon"], e["mag"], e["sev"]), (54.634, -160.218, 5.0, 0))
        self.assertEqual(e["title"], "Information: 45 miles SE of Sand Point, Alaska")
        self.assertTrue(e["url"].endswith("WEAK53.txt"))

    def test_ptwc(self):
        self.assertEqual(self.process("geo.tsunami-ptwc")["status"], "ok")

    def test_empty_feed_is_valid(self):
        body = b'<?xml version="1.0"?><feed xmlns="http://www.w3.org/2005/Atom"><title>x</title></feed>'
        from lib import pipeline
        from helpers import dataset
        ds = dataset("geo.tsunami-ntwc")
        res = self.parse("geo.tsunami-ntwc", body)
        pipeline.write(ds, res, self.ctx)      # no error (rule g)
        self.assertEqual(self.read("geo.tsunami-ntwc", "active.json")["events"], [])


if __name__ == "__main__":
    unittest.main()
