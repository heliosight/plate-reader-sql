# Plate-reader kinetic assay database

SQL (SQLite) reconstruction of the data model I used in the lab to keep 500+ plate-reader datasets collected over ten years in one place. This repository contains the SQL schema and the loading and cleaning scripts for three plate-reader formats (Tecan, Synergy, BMG). No lab data is included.

The data are fluorescence time courses (Thioflavin T assays of protein aggregation kinetics) from 96-well plates. Each instrument exports the same information in a different layout, so the loader maps all of them onto one long format: one row per run, well and time point.

## Files

| File | Purpose |
|---|---|
| `schema.sql` | Table definitions with keys, value ranges and allowed-value rules written as constraints |
| `parsers.py` | One parser per instrument layout; each returns `run_id, well, time_s, fluorescence` |
| `build_db.py` | Rebuilds `plate_reader.db` from scratch: schema, metadata, readings, summary check |
| `requirements.txt` | Python dependencies (`pandas`, `openpyxl`) |

## Data model

Seven tables: `experiments`, `buffers`, `samples`, `runs`, `wells`, `analytes`, `readings`.

- An experiment has many runs; a buffer is used by many runs.
- A run has many wells; a sample can be placed in many wells.
- Each well has many readings, keyed by run, well and time.
- Analyte concentrations are recorded per run and sample, by analyte and method.

Rules enforced by the schema include pH between 0 and 14, allowed plate formats, wavelength ranges, salt and salt concentration set together or not at all, one source file per run, and foreign keys between all tables.

## Running it

Expected input folders next to the scripts:

```
meta/       experiments.csv, buffers.csv, samples.csv, runs.csv, analytes.csv
wells/      one CSV well map per run (run_id, well, sample)
readings/   instrument export files (.xlsx), named in runs.measurement_file
```

Column names in each CSV match the table columns in `schema.sql`. The value in `runs.instrument` must start with `Tecan`, `Synergy` or `BMG`, which selects the parser.

```
pip install -r requirements.txt
python build_db.py
```

The script deletes and rebuilds `plate_reader.db` each time, so there are no duplicates. It prints one line per loaded run, reports missing files, and ends with a summary of readings, time points and empty values per run. A constraint violation stops the load.

## Source-to-target mapping (readings)

| Target field | Tecan | Synergy | BMG |
|---|---|---|---|
| `time_s` | rows labelled `120s` | clock time `0:01:00` | column headers like `1 h 5 min` |
| `well` | columns A1 to H12 | columns A1 to H12 | row labels `A01` to `H12`, normalized to `A1` |
| `fluorescence` | wide grid reshaped to long | wide grid reshaped to long | transposed grid reshaped to long |

BMG exports sometimes contain a glitch cycle, a mid-run column labelled `0 h` that duplicates the previous cycle. Any cycle whose time label jumps backward is dropped.

## Design notes

- Overflow flags and blank cells become NULL. This does not distinguish a saturated detector from a blank cell; storing a separate flag would be a natural extension.
- Metadata (`meta/`, `wells/`) is curated by hand. Only the readings are parsed from instrument files.
- The per-timepoint temperature column in Tecan exports is not loaded; the schema keeps start and run temperatures at run level.
