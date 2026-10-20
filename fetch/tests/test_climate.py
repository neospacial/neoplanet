"""Climate record adapters: ncei_cag, gistemp, gml_csv, nsidc, cpc_oni, cpc_nino_weekly, cpc_daily,
ozone_watch, bom_mjo (no fixture), star_gmsl (no fixture, fallback)."""
import unittest

from helpers import StoreCase, common, dataset
from adapters import climate  # noqa: E402  (helpers sets the path)


def last(rows):
    return rows[max(rows)]


class ClimateTest(StoreCase):
    def test_ncei(self):
        rows = self.parse("climate.temp-ncei")["series"]["rows"]
        self.assertEqual(rows[common.epoch(1850, 1)], [-0.43])

    def test_gistemp(self):
        rows = self.parse("climate.temp-gistemp")["series"]["rows"]
        self.assertEqual(rows[common.epoch(1880, 1)], [-0.19])
        self.assertEqual(max(rows), common.epoch(2026, 9))          # *** is missing

    def test_gml(self):
        self.assertEqual(last(self.parse("climate.co2-daily")["series"]["rows"]), [426.73])
        self.assertEqual(last(self.parse("climate.co2-monthly")["series"]["rows"]), [426.07, 429.55])
        self.assertEqual(last(self.parse("climate.ch4-global")["series"]["rows"]), [1934.57, 1942.12])
        self.assertEqual(self.parse("climate.sf6-global")["series"]["cols"][0]["unit"], "ppt")

    def test_nsidc(self):
        rows = self.parse("climate.seaice-north")["series"]["rows"]
        self.assertEqual(rows[common.epoch(2026, 10, 17)], [6.717])

    def test_oni(self):
        rows = self.parse("climate.oni")["series"]["rows"]
        self.assertEqual(rows[common.epoch(1950, 1)], [25.01, -1.32])      # DJF 1950: center month January
        self.assertEqual(rows[common.epoch(2026, 8)], [29.12, 2.16])       # JAS 2026: August

    def test_nino_weekly(self):
        rows = self.parse("climate.nino-weekly")["series"]["rows"]
        self.assertEqual(rows[common.epoch(2011, 6, 22)], [23.4, 0.6, 26.5, 0.1, 27.4, -0.2, 28.3, -0.5])
        self.assertEqual(last(rows)[5], 3.3)

    def test_cpc_daily(self):
        s = self.parse("climate.ao")["series"]
        self.assertAlmostEqual(last(s["rows"])[0], 2.708335528334634)
        self.assertEqual(s["cols"][0]["label"], "AO")

    def test_ozone_future_rows(self):
        r = self.parse("climate.ozone-hole")
        self.assertEqual(r["series"]["rows"][common.parse_iso("2026-12-31")][0], None)
        self.assertLess(r["newest"], max(r["series"]["rows"]))
        self.assertEqual(self.process("climate.ozone-hole")["status"], "ok")     # rule f allows future rows

    def test_mjo_format(self):
        body = (b"RMM values\nyear month day RMM1 RMM2 phase amplitude origin\n"
                b" 2026 10 18  0.512 -1.203  3  1.307 Final\n 2026 10 19 1.E36 1.E36 999 1.E36 Missing\n")
        rows = self.parse("climate.mjo", body)["series"]["rows"]
        self.assertEqual(rows[common.epoch(2026, 10, 18)], [0.512, -1.203, 3.0, 1.307])
        self.assertEqual(rows[common.epoch(2026, 10, 19)], [None, None, None, None])

    def test_gmsl_format(self):
        body = b"year,TOPEX/Poseidon,Jason-1\n1993.0110,-30.5,\n2026.5000,,95.2\n"
        rows = climate.parse_gmsl(body)
        self.assertEqual(list(rows.values()), [[-30.5], [95.2]])

    def test_gmsl_fallback_to_sla(self):
        self.process("ocean.sla")
        out = self.process("climate.gmsl")         # offline: no STAR fixture
        self.assertEqual(out["status"], "degraded")
        self.assertIn("fallback", out["message"])
        latest = self.read("climate.gmsl", "latest.json")
        self.assertIn("gmsl", latest["last"])

    def test_gmsl_no_data_at_all(self):
        self.assertEqual(self.process("climate.gmsl")["status"], "error")


if __name__ == "__main__":
    unittest.main()
