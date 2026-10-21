-- Plate-reader kinetic assay database (SQLite)
-- Parents first, then children.

CREATE TABLE experiments (
    exp_id    TEXT PRIMARY KEY,
    run_date  TEXT NOT NULL
);

CREATE TABLE buffers (
    buffer_id     TEXT PRIMARY KEY,
    buffer_agent  TEXT NOT NULL,
    buffer_mM     REAL NOT NULL,
    salt          TEXT,
    salt_mM       REAL,
    pH            REAL NOT NULL CHECK (pH BETWEEN 0 AND 14),
    CHECK ((salt IS NULL) = (salt_mM IS NULL))
);

CREATE TABLE samples (
    sample         TEXT PRIMARY KEY,
    content        TEXT NOT NULL
                   CHECK (content IN ('protein+ThT', 'ThT', 'buffer', 'water', 'empty')),
    peptide        TEXT,
    filtered       INTEGER CHECK (filtered IN (0, 1)),
    dilution_fold  INTEGER CHECK (dilution_fold BETWEEN 1 AND 64)
);

CREATE TABLE runs (
    run_id              TEXT PRIMARY KEY,
    exp_id              TEXT NOT NULL REFERENCES experiments(exp_id),
    run_reading         TEXT NOT NULL CHECK (run_reading IN ('top', 'bottom')),
    instrument          TEXT NOT NULL,
    plate_format        INTEGER NOT NULL CHECK (plate_format IN (24, 96, 384, 1536)),
    plate_temp_start_c  REAL NOT NULL CHECK (plate_temp_start_c BETWEEN 0 AND 99),
    temp_run_c          REAL NOT NULL CHECK (temp_run_c BETWEEN 0 AND 99),
    excitation_nm       INTEGER NOT NULL CHECK (excitation_nm BETWEEN 220 AND 900),
    emission_nm         INTEGER NOT NULL CHECK (emission_nm BETWEEN 220 AND 900),
    measurement_file    TEXT NOT NULL UNIQUE,
    buffer_id           TEXT NOT NULL REFERENCES buffers(buffer_id)
);

CREATE TABLE wells (
    run_id  TEXT NOT NULL REFERENCES runs(run_id),
    well    TEXT NOT NULL,
    sample  TEXT NOT NULL REFERENCES samples(sample),
    PRIMARY KEY (run_id, well)
);

CREATE TABLE analytes (
    run_id   TEXT NOT NULL REFERENCES runs(run_id),
    sample   TEXT NOT NULL REFERENCES samples(sample),
    analyte  TEXT NOT NULL CHECK (analyte IN ('Abeta42', 'ThT')),
    conc_uM  REAL NOT NULL CHECK (conc_uM >= 0),
    sd_uM    REAL CHECK (sd_uM >= 0),
    method   TEXT NOT NULL,
    PRIMARY KEY (run_id, sample, analyte, method)
);

CREATE TABLE readings (
    run_id        TEXT NOT NULL,
    well          TEXT NOT NULL,
    time_s        INTEGER NOT NULL CHECK (time_s >= 0),
    fluorescence  REAL,
    PRIMARY KEY (run_id, well, time_s),
    FOREIGN KEY (run_id, well) REFERENCES wells(run_id, well)
);
