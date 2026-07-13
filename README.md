# Drosophila Activity Analysis — GUI

> ⚠️ **This is a graphical interface, not a new analysis method.**
> It is a thin GUI layer and Python 3 port over the existing, published tool
> **[williamrowell/drosophila_activity_analysis](https://github.com/williamrowell/drosophila_activity_analysis)**
> by **William Rowell** (Howard Hughes Medical Institute / Janelia Research
> Campus). All of the science — how activity is aggregated, how sleep is defined
> (5+ consecutive minutes of no beam crossings), how dead flies are detected, and
> how the plots are built — comes from that original project. This repository
> only makes it easier to run: it wraps the original logic in a point-and-click
> web app, ports it from the archived Python 2.7 code to Python 3, and adds
> packaging/tests/Docker so it can be deployed. **Please cite the original work,
> not this wrapper** (see [Attribution](#attribution)).

A Streamlit web app for Trikinetics DAM/DEnM sleep & activity analysis. Instead
of hand-editing `.ini` files and running a script from the data folder, you fill
in a form, edit a genotype table, click **Run**, preview the plots inline, and
download the PDFs and Excel files.

**🌐 Run it online:** one-click deploy to Streamlit Community Cloud (free) →
[**Deploy this app**](https://share.streamlit.io/deploy?repository=mbsai/drosophila-activity-gui&branch=main&mainModule=app.py).
Sign in with GitHub, click **Deploy**, and you'll get a public
`*.streamlit.app` URL. Paste that URL here afterwards:

<!-- **Live app:** https://YOUR-APP-NAME.streamlit.app -->

## What it computes

For each experimental genotype (vs. the control genotype[s]):

- **Activity** — beam crossings per time bin, mean ± sem across flies.
- **Sleep** — minutes of sleep per bin (sleep = 5+ consecutive minutes of zero
  activity).
- **Environment** — light (lux), temperature (°C), relative humidity (%) from the
  DEnM.
- **Dead-fly removal** — flies with no activity across the check day are dropped.

Outputs: multi-page PDF plots, `*_activity.xlsx` / `*_sleep.xlsx` tables, and a
`dead_flies.txt` list — downloadable individually or as one zip.

## How to use it

### Option A — Docker (self-contained, nothing to install but Docker)

```bash
docker build -t dam-gui .
docker run -p 8501:8501 dam-gui
# open http://localhost:8501
```

To analyze data that lives on your machine, mount the folder and type that path
into the app's "Folder with Monitor#.txt files" box:

```bash
docker run -p 8501:8501 -v /path/to/your/data:/data dam-gui   # then type /data
```

### Option B — Python (local)

```bash
pip install -r requirements.txt
streamlit run app.py
```

### Option C — Deploy from GitHub (free public URL)

Push this repo to GitHub, then go to <https://share.streamlit.io> → **New app**,
pick the repo, set the main file to `app.py`, and deploy. See
[DEPLOY.md](DEPLOY.md) for the full walkthrough and notes.

### Using the app

1. **Data source** (sidebar): upload your `Monitor<n>.txt` files, or (when
   running locally/Docker) point to a folder. No data? Click **Generate sample
   data** for a synthetic 4-day dataset.
2. **Global config**: the environmental-monitor list and max monitor number.
3. **Protocol**: bin size, lights on/off, DD start, dead-fly check day, DEnM,
   effector, control genotype, gender.
4. **Genotypes**: one row per (monitor, channel range); repeat a genotype name to
   span multiple monitors.
5. **Run**: preview plots in the tabs and download results.

You can **import** an existing experiment `.ini` to prefill the form and
**export** the current settings back to an `.ini` compatible with the original
command-line tool.

## Requirements & footprint

No GPU or special hardware. A full run of the sample dataset takes ~0.5 s and
~180 MB RAM (mostly library load). Realistic experiments stay well under 1 GB,
so any laptop or the smallest free cloud tier is enough.

## Development

```bash
make setup     # install deps (incl. pytest)
make test      # run the regression tests
make run       # run the app locally
make dev       # live-reload dev container (edits reflect without rebuild)
```

Tests live in `tests/` and lock in the pipeline's behavior so future changes
fail loudly. CI runs them on every push (`.github/workflows/tests.yml`).

## Project layout

```
app.py                 Streamlit UI
make_sample_data.py    synthetic Trikinetics data generator
dam/                   Python 3 port of the original analysis modules
  file_io.py           read config/key + DAM/DEnM files; write Excel
  analyze.py           aggregate by genotype, dead-fly detection, sleep calc
  plot.py              build environment / activity / sleep figures
  pipeline.py          orchestrate a full run from Python dicts
tests/                 pytest regression tests
Dockerfile             self-contained image
docker-compose.yml     live-reload dev container
DEPLOY.md              deployment options (Docker / Streamlit Cloud / others)
```

## Data format

Standard Trikinetics monitor files: tab-separated, 42 fields per minute — field
2 = date (`DD Mon YY`), field 3 = time, field 4 = status, field 10 = light
status, fields 11–42 = 32 activity channels. DEnM files carry light/temp/humidity
in fields 14/19/24. Files must be named `Monitor<n>.txt`.

## Attribution

This project is a derivative work of:

> **drosophila_activity_analysis** — William Rowell, Howard Hughes Medical
> Institute / Janelia Research Campus, 2014–2020.
> <https://github.com/williamrowell/drosophila_activity_analysis>

The analysis logic in `dam/` is a Python 3 port of that project's `file_io.py`,
`analyze.py`, and `plot.py`. If you use this in published work, please cite the
original project and its author, not this GUI wrapper.

## License

Distributed under the **Janelia Research Campus Software Copyright 1.1** license,
the same license as the original project (Copyright © 2015, Howard Hughes Medical
Institute). See [LICENSE](LICENSE).
