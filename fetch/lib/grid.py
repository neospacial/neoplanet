"""Grid tools: regrid, cell counts, quantize, sparse encode, area means (plan 5.4, 6.2, 7.2).

A grid is a flat row-major list. Row 0 is the south row (lat0). Column 0 is
lon0. Cell centers: lat0 + i * d, lon0 + j * d.
"""
import math

from .store import encode_grid, decode_grid


def spec(d, west=-180.0, south=-90.0):
    """Return a grid header for d-degree cells that cover the globe.

    west and south are the cell edges. lat0 and lon0 are cell centers.
    """
    nlat = int(round((90.0 - south) / d))
    nlon = int(round(360 / d))
    return {"lat0": south + d / 2, "lon0": west + d / 2, "d": d, "nlat": nlat, "nlon": nlon}


def cell_index(g, lat, lon):
    """Return the flat index of the cell that contains (lat, lon), or None."""
    d = g["d"]
    i = int(math.floor((lat - (g["lat0"] - d / 2)) / d))
    if i == g["nlat"] and lat <= g["lat0"] - d / 2 + g["nlat"] * d + 1e-9:
        i = g["nlat"] - 1           # the north pole row goes into the last cell
    lon_west = g["lon0"] - d / 2
    j = int(math.floor(((lon - lon_west) % 360.0) / d))
    if j == g["nlon"]:
        j = 0
    if not (0 <= i < g["nlat"] and 0 <= j < g["nlon"]):
        return None
    return i * g["nlon"] + j


def regrid_max(points, g):
    """Put (lat, lon, value) points into the cells of g. Each cell keeps the maximum."""
    out = [None] * (g["nlat"] * g["nlon"])
    for lat, lon, v in points:
        if v is None:
            continue
        k = cell_index(g, lat, lon)
        if k is None:
            continue
        if out[k] is None or v > out[k]:
            out[k] = v
    return out


def count_cells(points, g):
    """Count (lat, lon) points in each cell (fire density, grid.aggregate = count)."""
    out = [0] * (g["nlat"] * g["nlon"])
    for lat, lon in points:
        k = cell_index(g, lat, lon)
        if k is not None:
            out[k] += 1
    return out


def from_points(points, g):
    """Put (lat, lon, value) points on the grid. Points that do not hit a cell center are kept by cell."""
    out = [None] * (g["nlat"] * g["nlon"])
    for lat, lon, v in points:
        k = cell_index(g, lat, lon)
        if k is not None:
            out[k] = v
    return out


def area_mean(values, g, box=None):
    """Area-weighted mean (weight cos(lat)). Skip None. box = (lat_s, lat_n, lon_w, lon_e)."""
    s = w = 0.0
    for i in range(g["nlat"]):
        lat = g["lat0"] + i * g["d"]
        if box and not (box[0] <= lat <= box[1]):
            continue
        cw = math.cos(math.radians(lat))
        row = i * g["nlon"]
        for j in range(g["nlon"]):
            v = values[row + j]
            if v is None:
                continue
            if box:
                lon = ((g["lon0"] + j * g["d"]) + 180.0) % 360.0 - 180.0
                if not _lon_in(lon, box[2], box[3]):
                    continue
            s += v * cw
            w += cw
    return s / w if w else None


def _lon_in(lon, west, east):
    if west <= east:
        return west <= lon <= east
    return lon >= west or lon <= east


def combine(grids, how):
    """Combine grids cell by cell: 'max', 'mean', or 'sum'. Skip None."""
    n = len(grids[0])
    out = [None] * n
    for k in range(n):
        vals = [g[k] for g in grids if g[k] is not None]
        if not vals:
            continue
        if how == "max":
            out[k] = max(vals)
        elif how == "sum":
            out[k] = sum(vals)
        else:
            out[k] = sum(vals) / len(vals)
    return out


def snapshot(sid, t, g, values, q, fill=None):
    """Make a grid shard (plan 5.4)."""
    return {"v": 1, "id": sid, "t": t, "grid": g, "enc": "sparse-rle", "q": q, "fill": fill,
            "data": encode_grid(values, q, fill)}


def values_of(shard, data=None):
    n = shard["grid"]["nlat"] * shard["grid"]["nlon"]
    return decode_grid(data if data is not None else shard["data"], shard["q"], n, shard.get("fill"))
