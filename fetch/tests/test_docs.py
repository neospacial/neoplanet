"""Repository rules: docs agree with sources.json, no key in any file, data is ignored."""
import os
import re
import subprocess
import sys
import unittest

from helpers import REGISTRY, ROOT


class DocsTest(unittest.TestCase):
    def test_sources_md_is_current(self):
        r = subprocess.run([sys.executable, os.path.join(ROOT, "tools", "sources_md.py"), "--check"],
                           capture_output=True, text=True)
        self.assertEqual(r.returncode, 0, r.stdout)

    def test_every_dataset_has_an_adapter_name_and_retention(self):
        for ds in REGISTRY["datasets"]:
            self.assertTrue(ds.get("adapter"), ds["id"])
            self.assertTrue(ds.get("retention"), ds["id"])

    def test_gitignore_has_data(self):
        with open(os.path.join(ROOT, ".gitignore")) as f:
            lines = f.read().split()
        self.assertIn("data/", lines)
        self.assertIn("_site/", lines)

    def test_no_key_like_values_in_code(self):
        pat = re.compile(r"api_key=(?!\{NASA_API_KEY\}|DEMO_KEY|\*\*\*)[A-Za-z0-9]{20,}")
        for base in ("fetch", ".github", "tools"):
            for dirpath, _, files in os.walk(os.path.join(ROOT, base)):
                for f in files:
                    if f.endswith((".py", ".yml", ".json", ".md", ".html")):
                        with open(os.path.join(dirpath, f), encoding="utf-8", errors="ignore") as fh:
                            self.assertIsNone(pat.search(fh.read()), os.path.join(dirpath, f))

    def test_version_file(self):
        with open(os.path.join(ROOT, "VERSION")) as f:
            self.assertRegex(f.read().strip(), r"^\d+\.\d+\.\d+$")


if __name__ == "__main__":
    unittest.main()
