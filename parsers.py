"""Parsers for plate-reader export files.

One parser per instrument layout. Each returns a long-format DataFrame with
the columns run_id, well, time_s, fluorescence (one row per well and time point).
"""
import re

import pandas as pd

WELLS = [f"{r}{c}" for r in "ABCDEFGH" for c in range(1, 13)]


def finish(long, run_id):
    """Common last step: numeric fluorescence, run id column, fixed column order."""
    # Overflow flags and blank cells become NULL
    long["fluorescence"] = pd.to_numeric(long["fluorescence"], errors="coerce")
    long.insert(0, "run_id", run_id)
    return long[["run_id", "well", "time_s", "fluorescence"]]


def parse_tecan(path, run_id):
    # rows = time points ("120s"), 96 wells side by side, metadata footer
    raw = pd.read_excel(path, header=None)
    data = raw[raw[0].astype(str).str.fullmatch(r"\d+s")].iloc[:, :98]
    data.columns = ["time", "temp"] + WELLS
    data["time_s"] = data["time"].str.rstrip("s").astype(int)
    long = data.melt(id_vars="time_s", value_vars=WELLS,
                     var_name="well", value_name="fluorescence")
    return finish(long, run_id)


def parse_synergy(path, run_id):
    # header row starting with "Time", time as clock value 0:01:00
    raw = pd.read_excel(path, header=None)
    start = raw.index[raw[0] == "Time"][0]
    data = raw.iloc[start + 1:].copy()
    data.columns = raw.iloc[start]
    data = data.dropna(subset=["Time"])
    data["time_s"] = [t.hour * 3600 + t.minute * 60 + t.second for t in data["Time"]]
    long = data.melt(id_vars="time_s", value_vars=WELLS,
                     var_name="well", value_name="fluorescence")
    return finish(long, run_id)


def to_seconds(label):
    h = re.search(r"(\d+)\s*h", label)
    m = re.search(r"(\d+)\s*min", label)
    return (int(h.group(1)) if h else 0) * 3600 + (int(m.group(1)) if m else 0) * 60


def parse_bmg(path, run_id):
    # transposed: wells are rows (A01), times are columns ("1 h 5 min");
    # the "Time" row can sit at the top or below a metadata block, so find it
    raw = pd.read_excel(path, header=None, sheet_name=0)
    trow = raw.index[raw[1] == "Time"][0]
    times = [to_seconds(str(t)) for t in raw.iloc[trow, 2:].dropna()]
    data = raw[raw[0].astype(str).str.fullmatch(r"[A-H]\d\d")].iloc[:, :2 + len(times)].copy()
    data.columns = ["well", "content"] + list(range(len(times)))
    # drop glitch cycles whose time label jumps back
    # (a mid-run "0 h" column is a copy of the previous cycle)
    keep, last = [], -1
    for i, t in enumerate(times):
        if t > last:
            keep.append(i)
            last = t
    data = data[["well", "content"] + keep]
    data.columns = ["well", "content"] + [times[i] for i in keep]
    times = [times[i] for i in keep]
    data["well"] = data["well"].str[0] + data["well"].str[1:].astype(int).astype(str)
    long = data.melt(id_vars="well", value_vars=times,
                     var_name="time_s", value_name="fluorescence")
    long["time_s"] = long["time_s"].astype(int)
    return finish(long, run_id)


# runs.instrument must start with one of these names
PARSERS = {"Tecan": parse_tecan, "Synergy": parse_synergy, "BMG": parse_bmg}
