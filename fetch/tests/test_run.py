"""End-to-end offline run (Phase 1 acceptance) and the tier schedule."""
import io
import json
import os
import shutil
import tempfile
import unittest
from contextlib import redirect_stdout

from helpers import ROOT, common
import run


class RunTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix="pdd-run-")
        self.out = os.path.join(self.tmp, "gh_output")
        self.env = dict(os.environ)
        os.environ["GITHUB_OUTPUT"] = self.out
        os.environ.pop("GITHUB_STEP_SUMMARY", None)

    def tearDown(self):
        os.environ.clear()
        os.environ.update(self.env)
        shutil.rmtree(self.tmp, ignore_errors=True)

    @staticmethod
    def load(path):
        with open(path, encoding="utf-8") as f:
            return json.load(f)

    def run_offline(self, now="2026-10-20T18:00:00Z", *extra):
        open(self.out, "w").close()
        buf = io.StringIO()
        with redirect_stdout(buf):
            code = run.main(["--tier", "all", "--offline", os.path.join(ROOT, "fixtures"),
                             "--now", now, "--data", self.tmp + "/data", *extra])
        self.assertEqual(code, 0)
        with open(self.out) as f:
            outputs = dict(line.strip().split("=", 1) for line in f if "=" in line)
        return buf.getvalue(), outputs

    def test_acceptance(self):
        text, outputs = self.run_offline()
        self.assertIn("Total store size:", text)
        man = self.load(os.path.join(self.tmp, "data", "manifest.json"))
        self.assertEqual(man["v"], 1)
        self.assertTrue(man["deploy"])
        self.assertLess(man["total_bytes"], 150 * 1024 * 1024)
        for sid, e in man["datasets"].items():
            self.assertIn(e["status"], ("ok", "stale", "degraded", "error"), sid)
        reg = run.load_registry()
        for ds in reg["datasets"]:
            if ds["adapter"].startswith("swpc_"):
                e = man["datasets"][ds["id"]]
                self.assertEqual(e["status"], "ok", ds["id"])
                for tier, names in e["files"].items():
                    for n in names:
                        p = os.path.join(self.tmp, "data", e["path"], "" if tier == "root" else tier, n + ".json")
                        self.load(p)      # each listed file is valid JSON
        self.assertEqual(outputs["changed"], "true")
        self.assertEqual(outputs["deploy"], "true")
        self.assertFalse(os.path.exists(os.path.join(self.tmp, "data", "_state", "http.json")))

    def test_second_run_has_no_change(self):
        self.run_offline()
        _, outputs = self.run_offline()
        self.assertEqual(outputs["changed"], "false")
        self.assertEqual(outputs["deploy"], "false")

    def test_only_filter(self):
        text, _ = self.run_offline("2026-10-20T18:00:00Z", "--only", "space.kp,space.dst")
        self.assertIn("4 datasets", text)     # the prefix space.kp also selects kp-1m and kp-forecast
        man = self.load(os.path.join(self.tmp, "data", "manifest.json"))
        self.assertEqual(man["datasets"]["space.dst"]["status"], "ok")
        self.assertEqual(man["datasets"]["space.xray"]["status"], "error")

    def test_due_tiers(self):
        t = lambda s: common.parse_iso(s)
        now = t("2026-10-20T06:13:00Z")       # Tuesday
        self.assertEqual(run.due_tiers({}, now), ["30m", "1h", "1d", "1w"])
        last = {"30m": now - 1800, "1h": now - 1800, "1d": t("2026-10-20T05:13:00Z"), "1w": t("2026-10-19T05:13:00Z")}
        self.assertEqual(run.due_tiers(last, now), ["30m"])
        last["1h"] = now - 3600
        self.assertEqual(run.due_tiers(last, now), ["30m", "1h"])
        early = t("2026-10-21T04:43:00Z")
        self.assertNotIn("1d", run.due_tiers(last, early))
        self.assertIn("1d", run.due_tiers(last, t("2026-10-21T05:13:00Z")))
        self.assertIn("1w", run.due_tiers(last, t("2026-10-26T05:13:00Z")))   # Monday


if __name__ == "__main__":
    unittest.main()
