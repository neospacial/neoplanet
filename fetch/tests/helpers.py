"""Test helpers. The tests use the fixtures only. They do not use the network."""
import json
import os
import shutil
import sys
import tempfile
import unittest

FETCH = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ROOT = os.path.dirname(FETCH)
if FETCH not in sys.path:
    sys.path.insert(0, FETCH)

from lib import common, pipeline                    # noqa: E402
from lib.http import OfflineClient                  # noqa: E402
from lib.store import Store                          # noqa: E402
import adapters                                      # noqa: E402

FIXTURES = os.path.join(ROOT, "fixtures")
NOW = common.parse_iso("2026-10-20T18:00:00Z")

with open(os.path.join(ROOT, "sources.json"), encoding="utf-8") as _f:
    REGISTRY = json.load(_f)


def dataset(sid):
    for ds in REGISTRY["datasets"]:
        if ds["id"] == sid:
            return json.loads(json.dumps(ds))
    raise KeyError(sid)


def fixture_bytes(ds_or_name):
    name = ds_or_name["fixture"] if isinstance(ds_or_name, dict) else ds_or_name
    with open(os.path.join(FIXTURES, os.path.basename(name)), "rb") as f:
        return f.read()


class StoreCase(unittest.TestCase):
    """A test case with an empty store in a temporary folder and a frozen clock."""

    now = NOW

    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix="pdd-test-")
        self.clock = common.Clock(self.now)
        self.store = Store(self.tmp, self.clock, env={})
        import run   # noqa: F401  (adds nothing; makes sure run.py imports)
        from run import fixture_map
        self.client = OfflineClient(FIXTURES, fixture_map(REGISTRY, self.now, {}))
        self.ctx = pipeline.Context(self.clock, self.client, self.store, offline=True, env={},
                                    log=lambda *a: None, sleep=lambda s: None)

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def parse(self, sid, body=None):
        ds = dataset(sid)
        _, parse = adapters.get(ds["adapter"])
        return parse(ds, body if body is not None else fixture_bytes(ds), self.ctx)

    def process(self, sid, ds=None):
        ds = ds or dataset(sid)
        return pipeline.process(ds, adapters, self.ctx)

    def read(self, sid, rel):
        return self.store.read(dataset(sid), rel)
