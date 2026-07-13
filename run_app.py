"""
Desktop launcher for the packaged Windows build.

When frozen with PyInstaller this becomes the .exe entry point: it starts the
Streamlit server locally and opens the app in the default web browser. Only the
packaged executable uses this file — the cloud/CLI deployments run
``streamlit run app.py`` directly.
"""

import os
import sys
import threading
import time
import webbrowser

PORT = "8501"
URL = "http://localhost:%s" % PORT


def _bundle_dir():
    """Directory that holds app.py / dam / make_sample_data.py at runtime."""
    # PyInstaller sets _MEIPASS to the unpacked bundle dir (onefile) or the
    # _internal dir (onedir). Fall back to this file's dir when unfrozen.
    return getattr(sys, "_MEIPASS", os.path.dirname(os.path.abspath(__file__)))


def _open_browser():
    # give the server a moment to come up before opening the tab
    time.sleep(3)
    webbrowser.open(URL)


def main():
    base = _bundle_dir()
    # make `import dam` / `import make_sample_data` resolve from the bundle
    if base not in sys.path:
        sys.path.insert(0, base)

    print("=" * 60)
    print(" Drosophila Activity Analysis")
    print(" Opening %s in your browser..." % URL)
    print(" Keep this window open while you use the app.")
    print(" Close this window to stop the app.")
    print("=" * 60)

    threading.Thread(target=_open_browser, daemon=True).start()

    import streamlit.web.cli as stcli
    sys.argv = [
        "streamlit", "run", os.path.join(base, "app.py"),
        "--server.port", PORT,
        "--server.headless", "true",          # we open the browser ourselves
        "--browser.gatherUsageStats", "false",
        "--global.developmentMode", "false",
    ]
    sys.exit(stcli.main())


if __name__ == "__main__":
    main()
