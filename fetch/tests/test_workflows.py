"""Workflow files: schedule, permissions, secrets by name only, cache keys, Pages deploy."""
import os
import re
import unittest

from helpers import ROOT

WF = os.path.join(ROOT, ".github", "workflows")


def read(name):
    with open(os.path.join(WF, name), encoding="utf-8") as f:
        return f.read()


class WorkflowTest(unittest.TestCase):
    def test_run(self):
        s = read("run.yml")
        self.assertIn('cron: "13,43 * * * *"', s)
        for perm in ("contents: write", "pages: write", "id-token: write", "actions: write"):
            self.assertIn(perm, s)
        self.assertIn("NASA_API_KEY: ${{ secrets.NASA_API_KEY }}", s)
        self.assertIn("FIRMS_MAP_KEY: ${{ secrets.FIRMS_MAP_KEY }}", s)
        self.assertIn("restore-keys: store-", s)
        self.assertIn("key: store-${{ github.run_id }}", s)
        self.assertIn("actions/upload-pages-artifact@", s)
        self.assertIn("actions/deploy-pages@", s)
        self.assertIn("name: github-pages", s)
        self.assertIn("group: pipeline", s)
        self.assertIn("cancel-in-progress: false", s)
        self.assertIn("--exclude '_state/'", s)

    def test_no_secret_values(self):
        for name in os.listdir(WF):
            s = read(name)
            for m in re.finditer(r"(NASA_API_KEY|FIRMS_MAP_KEY):\s*(.+)", s):
                self.assertTrue(m.group(2).strip().startswith("${{ secrets."), (name, m.group(0)))

    def test_test_and_audit(self):
        self.assertIn("python -m unittest", read("test.yml"))
        self.assertIn("--offline fixtures", read("test.yml"))
        self.assertIn("tools/audit/audit.py", read("audit.yml"))


if __name__ == "__main__":
    unittest.main()
