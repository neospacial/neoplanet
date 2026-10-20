"""Shared helpers: clock, durations, URL placeholders, key masking, atomic write.

All times are Unix seconds in UTC.
"""
import calendar
import datetime as dt
import json
import os
import re
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

KEY_NAMES = ("NASA_API_KEY", "FIRMS_MAP_KEY")
KEY_FALLBACK = {"NASA_API_KEY": "DEMO_KEY"}

DAY = 86400
TIER_SECONDS = {"30m": 1800, "1h": 3600, "1d": DAY, "1w": 7 * DAY}


class Clock:
    """The run clock. Tests freeze it with --now."""

    def __init__(self, frozen=None):
        self.frozen = frozen

    def now(self):
        if self.frozen is not None:
            return self.frozen
        return int(dt.datetime.now(dt.timezone.utc).timestamp())


def read_version():
    try:
        with open(os.path.join(ROOT, "VERSION"), encoding="utf-8") as f:
            return f.read().strip()
    except OSError:
        return "0.0.0"


def repo_url():
    """Return the repository URL for the User-Agent. No email."""
    url = os.environ.get("REPO_URL")
    if url:
        return url
    repo = os.environ.get("GITHUB_REPOSITORY")
    if repo:
        server = os.environ.get("GITHUB_SERVER_URL", "https://github.com")
        return f"{server}/{repo}"
    return "https://github.com"


def user_agent(template=None):
    template = template or "public-data-dashboard/{VERSION} (+{REPO_URL})"
    return template.replace("{VERSION}", read_version()).replace("{REPO_URL}", repo_url())


# ----------------------------------------------------------------- time

def parse_iso(text):
    """Parse an ISO time. A time with no zone is UTC. Return Unix seconds (int)."""
    s = text.strip().replace(" ", "T", 1)
    if s.endswith("Z"):
        s = s[:-1] + "+00:00"
    if len(s) == 10:
        s += "T00:00:00"
    d = dt.datetime.fromisoformat(s)
    if d.tzinfo is None:
        d = d.replace(tzinfo=dt.timezone.utc)
    return int(d.timestamp())


def iso(t):
    return dt.datetime.fromtimestamp(int(t), dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def ymd(t):
    return dt.datetime.fromtimestamp(int(t), dt.timezone.utc).strftime("%Y-%m-%d")


def ym(t):
    return dt.datetime.fromtimestamp(int(t), dt.timezone.utc).strftime("%Y-%m")


def utc(t):
    return dt.datetime.fromtimestamp(int(t), dt.timezone.utc)


def epoch(year, month=1, day=1, hour=0, minute=0, second=0):
    return calendar.timegm((year, month, day, hour, minute, second, 0, 0, 0))


def day_start(t):
    return int(t) - int(t) % DAY


def month_start(t):
    d = utc(t)
    return epoch(d.year, d.month)


def next_month(t):
    d = utc(t)
    return epoch(d.year + (d.month == 12), d.month % 12 + 1)


def year_start(t):
    return epoch(utc(t).year)


def week_start(t):
    """Monday 00:00 UTC of the week of t."""
    d0 = day_start(t)
    return d0 - utc(d0).weekday() * DAY


_DUR = re.compile(r"^(\d+)\s*([mhdwy])$")
_UNIT = {"m": 60, "h": 3600, "d": DAY, "w": 7 * DAY, "y": 365 * DAY}


def duration(text):
    """Convert '30m', '1h', '7d', '1y' to seconds. Return None for other values."""
    if not isinstance(text, str):
        return None
    m = _DUR.match(text.strip())
    if not m:
        return None
    return int(m.group(1)) * _UNIT[m.group(2)]


# ----------------------------------------------------------------- URLs and keys

def expand_url(url, now, env=None, extra=None):
    """Replace the placeholders in a URL.

    Return (url, fallback_used). fallback_used is True when a key secret is
    not set and the URL uses the fallback value.
    """
    env = os.environ if env is None else env
    today = utc(now).date()
    subs = {
        "D0": today.isoformat(),
        "D-7": (today - dt.timedelta(days=7)).isoformat(),
        "D-30": (today - dt.timedelta(days=30)).isoformat(),
        "Y": str(today.year),
    }
    subs.update(extra or {})
    fallback = False
    for name in KEY_NAMES:
        value = env.get(name) or ""
        if not value and name in KEY_FALLBACK:
            value = KEY_FALLBACK[name]
            if "{" + name + "}" in url:
                fallback = True
        subs[name] = value

    def rep(m):
        k = m.group(1)
        return str(subs[k]) if k in subs else m.group(0)

    return re.sub(r"\{([A-Z0-9_\-]+)\}", rep, url), fallback


def secret_values(env=None):
    env = os.environ if env is None else env
    out = []
    for name in KEY_NAMES:
        v = env.get(name)
        if v and v not in KEY_FALLBACK.values():
            out.append(v)
    return out


def mask(text, env=None):
    """Replace each key value in text with '***'."""
    if text is None:
        return text
    s = str(text)
    for v in secret_values(env):
        s = s.replace(v, "***")
    return s


# ----------------------------------------------------------------- files

def dumps(obj):
    return json.dumps(obj, separators=(",", ":"), ensure_ascii=False, allow_nan=False)


def atomic_write_bytes(path, data):
    """Write data to path through a temporary file and a rename.

    Return True if the file content changed.
    """
    try:
        with open(path, "rb") as f:
            if f.read() == data:
                return False
    except OSError:
        pass
    d = os.path.dirname(path)
    os.makedirs(d, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=d, prefix=".tmp-")
    try:
        with os.fdopen(fd, "wb") as f:
            f.write(data)
        os.replace(tmp, path)
    except BaseException:
        try:
            os.unlink(tmp)
        except OSError:
            pass
        raise
    return True


def write_json(path, obj, env=None):
    """Write obj as compact JSON. Mask key values. Return True if changed."""
    text = mask(dumps(obj), env)
    return atomic_write_bytes(path, text.encode("utf-8"))


def read_json(path, default=None):
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except (OSError, ValueError):
        return default
