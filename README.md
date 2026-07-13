# Drosophila Activity Analysis — GUI

A Streamlit graphical interface for
[williamrowell/drosophila_activity_analysis](https://github.com/williamrowell/drosophila_activity_analysis),
the Trikinetics DAM/DEnM sleep & activity toolkit. The original tool is an
archived Python 2.7 command-line program; this project ports the analysis to
Python 3 (modern pandas) and wraps it in a point-and-click web app.

Instead of hand-editing `.ini` files and running a script from the data folder,
you fill in a form, edit a genotype table, click **Run**, and preview the
activity/sleep/environment plots inline — then download the PDFs and Excel
files.

## What it does

For each experimental genotype (vs. the control genotype[s]) it computes:

- **Activity** — beam crossings per time bin, mean ± sem across flies.
- **Sleep** — minutes of sleep per bin, where sleep = 5+ consecutive minutes of
  zero activity.
- **Environment** — light (lux), temperature (°C) and relative humidity (%) from
  the DEnM.
- **Dead-fly removal** — flies with no activity across the check day are dropped.

Outputs: multi-page PDF plots, `*_activity.xlsx` / `*_sleep.xlsx` tables, and a
`dead_flies.txt` list — all downloadable as a single zip.

## Setup

```bash
pip install -r requirements.txt
```

## Run

```bash
streamlit run app.py
```

Then in the browser:

1. **Data source** (sidebar) — point to a folder containing your
   `Monitor<n>.txt` files, or upload them. No data? Click **Generate sample
   data** to create a synthetic 4-day dataset.
2. **Global config** — the environmental-monitor list and max monitor number.
3. **Protocol** — bin size, lights on/off, DD start, dead-fly check day, DEnM,
   effector, control genotype, gender.
4. **Genotypes** — one row per (monitor, channel range); repeat a genotype name
   to span multiple monitors.
5. **Run** — preview plots in the tabs and download results.

You can **import** an existing experiment `.ini` to prefill the form, and
**export** the current settings back to an `.ini` compatible with the original
CLI.

## Trying it without real data

```bash
python make_sample_data.py        # writes ./sample_data/
streamlit run app.py              # then click "Generate sample data" or point to ./sample_data
```

## Project layout

```
app.py                 Streamlit UI
make_sample_data.py    synthetic Trikinetics data generator
dam/
  file_io.py           read config/key + DAM/DEnM files; write Excel
  analyze.py           aggregate by genotype, dead-fly detection, sleep calc
  plot.py              build environment / activity / sleep figures
  pipeline.py          orchestrate a full run from Python dicts
repo/                  the original (archived) Python 2 project, for reference
```

## Data format

Standard Trikinetics monitor files: tab-separated, 42 fields per minute — field
2 = date (`DD Mon YY`), field 3 = time, field 4 = status, field 10 = light
status, fields 11–42 = 32 activity channels. DEnM files carry light/temp/humidity
in fields 14/19/24. Files must be named `Monitor<n>.txt`.
