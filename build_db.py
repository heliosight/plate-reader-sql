"""Rebuild abeta.db from scratch: schema, metadata CSVs, then instrument readings.

Run from the folder that contains meta/, wells/ and readings/:
    python build_db.py
"""
import glob
import os
import sqlite3

import pandas as pd

from parsers import PARSERS

DB = "plate_reader.db"


def load_csv(con, csv_path, table):
    pd.read_csv(csv_path).to_sql(table, con, if_exists="append", index=False)


def main():
    if os.path.exists(DB):
        os.remove(DB)  # always start clean, so no duplicates
    con = sqlite3.connect(DB)
    con.execute("PRAGMA foreign_keys = ON")

    # 1. Schema
    with open("schema.sql") as f:
        con.executescript(f.read())

    # 2. Metadata (parents before children, so foreign keys resolve)
    for table in ["experiments", "buffers", "samples", "runs"]:
        load_csv(con, f"meta/{table}.csv", table)
    for path in sorted(glob.glob("wells/*.csv")):
        load_csv(con, path, "wells")
    load_csv(con, "meta/analytes.csv", "analytes")
    con.commit()

    # 3. Readings: every run in `runs`, parser chosen by instrument
    runs = pd.read_sql("SELECT run_id, instrument, measurement_file FROM runs", con)
    for run_id, instrument, file in runs.itertuples(index=False):
        path = f"readings/{file}"
        if not os.path.exists(path):
            print("MISSING FILE:", run_id, file)
            continue
        parse = next(p for name, p in PARSERS.items() if instrument.startswith(name))
        parse(path, run_id).to_sql("readings", con, if_exists="append", index=False)
        print("loaded", run_id)
    con.commit()

    # 4. Checks
    summary = pd.read_sql("""
        SELECT run_id, COUNT(*) AS n_readings, COUNT(*) / 96 AS n_timepoints,
               SUM(fluorescence IS NULL) AS n_empty
        FROM readings GROUP BY run_id
    """, con)
    print(summary.to_string(index=False))
    con.close()


if __name__ == "__main__":
    main()
