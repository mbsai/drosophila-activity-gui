# Deploying the GUI

The app is a small pandas + matplotlib + Streamlit program. It needs **no GPU
and no special hardware** — a benchmark run (4 days × 3 monitors × 32 channels)
finishes in ~0.5 s using ~180 MB of RAM, most of which is just the Python
libraries loading. Any laptop or the smallest free cloud tier is plenty.

Rough sizing for real data: each monitor-day of per-minute activity is ~46k
numbers; even a large experiment (10 monitors × several weeks) stays well under
1 GB. CPU is single-threaded and the work is seconds, not minutes.

There are three ways to run it, from least to most "hands-off".

---

## 1. Local, self-contained with Docker (recommended for a lab machine)

This bundles Python and every dependency into one image — nothing to install on
the host but Docker itself.

```bash
docker build -t dam-gui .
docker run -p 8501:8501 dam-gui
# open http://localhost:8501
```

To analyze real data that lives on the host, mount the folder and use that path
in the app's "Folder with Monitor#.txt files" box:

```bash
docker run -p 8501:8501 -v /path/to/your/data:/data dam-gui
# then type /data in the folder box
```

## 2. Local without Docker

```bash
pip install -r requirements.txt
streamlit run app.py
```

(Use a virtual environment to keep it isolated: `python -m venv .venv && source
.venv/bin/activate` first.)

## 3. Deploy from GitHub — Streamlit Community Cloud (free, zero servers)

1. Push this project to a GitHub repo.
2. Go to https://share.streamlit.io, sign in with GitHub, and click
   **New app**.
3. Pick the repo/branch and set the main file to `app.py`. It reads
   `requirements.txt` automatically.
4. Deploy — you get a public `*.streamlit.app` URL.

The free tier gives ~1 GB RAM (fine here) and the app sleeps after inactivity,
waking on the next visit.

**Important caveat for any cloud host:** there is no local disk the visitor can
browse, so the **"Folder with Monitor#.txt files" box does not work in the
cloud** — visitors must use the **"…or upload Monitor#.txt files"** uploader
instead (or click *Generate sample data* to try it). The folder-path option is
only meaningful when the app runs on the same machine as the data.

Other equivalent "deploy from a Git repo" hosts that work the same way:
Hugging Face Spaces (Streamlit SDK), Render, Railway, or Fly.io (the last three
can use the `Dockerfile` above).

---

## Which should you pick?

- **Just you / your lab, data on your machine** → Docker (path #1). Self-contained,
  works offline, folder-path works.
- **Share a link with collaborators, small data they upload** → Streamlit
  Community Cloud (path #3).
- **Full control / private server** → the `Dockerfile` on Render/Railway/Fly.io.
