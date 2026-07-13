"""
Streamlit GUI for the Drosophila activity analysis pipeline.

Run with:
    streamlit run app.py
"""

import datetime as dt
import io
import os
import tempfile
import zipfile

import matplotlib
matplotlib.use('Agg')  # headless backend for server-side rendering

import pandas as pd
import streamlit as st

from dam import file_io, pipeline

st.set_page_config(page_title="Drosophila Activity Analysis",
                   page_icon="🪰", layout="wide")

HERE = os.path.dirname(os.path.abspath(__file__))
DEFAULT_ENV_MONITORS = "24, 25, 26, 27, 28, 29, 30, 65, 66, 92, 93"

# --------------------------------------------------------------------------- #
# helpers
# --------------------------------------------------------------------------- #
def _default_genotype_df():
    return pd.DataFrame([
        {"Genotype": "control_GAL4", "Monitor": 1, "First channel": 1, "Last channel": 16},
        {"Genotype": "experimental_line", "Monitor": 1, "First channel": 17, "Last channel": 32},
        {"Genotype": "experimental_line", "Monitor": 2, "First channel": 1, "Last channel": 16},
    ])


_PROTOCOL_DEFAULTS = {
    "k_bin": 30, "k_lon": 9, "k_loff": 21, "k_gender": "f",
    "k_dd": 0, "k_check": 1, "k_denm": None,
    "k_effector": "dTrpA1", "k_control": "control_GAL4",
}


def _ensure_state():
    st.session_state.setdefault("genotype_df", _default_genotype_df())
    st.session_state.setdefault("result", None)
    st.session_state.setdefault("out_dir", None)
    for key, val in _PROTOCOL_DEFAULTS.items():
        st.session_state.setdefault(key, val)


def _list_monitors(data_dir):
    if not data_dir or not os.path.isdir(data_dir):
        return []
    nums = []
    for name in os.listdir(data_dir):
        if name.startswith("Monitor") and name.endswith(".txt"):
            stem = name[len("Monitor"):-len(".txt")]
            if stem.isdigit():
                nums.append(int(stem))
    return sorted(nums)


def _genotype_dict_from_df(df):
    genotype_dict = {}
    for _, row in df.iterrows():
        name = str(row["Genotype"]).strip()
        if not name:
            continue
        pos = (int(row["Monitor"]), int(row["First channel"]), int(row["Last channel"]))
        genotype_dict.setdefault(name, []).append(pos)
    return genotype_dict


def _build_ini(protocol, genotype_df):
    lines = ["[Protocol]"]
    for key in ("bin", "lights_on", "lights_off", "DD", "check_day", "DEnM",
                "effector", "control_genotype", "gender"):
        lines.append("%s: %s" % (key, protocol[key]))
    lines.append("")
    lines.append("[Genotypes]")
    gd = _genotype_dict_from_df(genotype_df)
    for name, positions in gd.items():
        pos_str = ", ".join("%d.%d-%d" % p for p in positions)
        lines.append("%s: %s" % (name, pos_str))
    return "\n".join(lines) + "\n"


def _zip_output(out_dir):
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        for root, _, files in os.walk(out_dir):
            for name in files:
                full = os.path.join(root, name)
                zf.write(full, os.path.relpath(full, out_dir))
    buf.seek(0)
    return buf.getvalue()


# --------------------------------------------------------------------------- #
# sidebar: data source + global config
# --------------------------------------------------------------------------- #
_ensure_state()

st.sidebar.title("🪰 Setup")

st.sidebar.header("1. Data source")
# Upload works everywhere (local or cloud); a local folder path only works when
# the app runs on the same machine as the data, so upload is the default.
data_mode = st.sidebar.radio(
    "Where is your data?",
    ["Upload files", "Local folder"],
    key="data_mode",
    help="Upload works everywhere, including cloud deployments. 'Local folder' "
         "only works when the app runs on the same machine as your data.",
)

uploads = None
data_dir = ""
if data_mode == "Upload files":
    uploads = st.sidebar.file_uploader(
        "Monitor#.txt files", type="txt", accept_multiple_files=True,
        help="Upload every Monitor<n>.txt file for this experiment.",
    )
else:
    data_dir = st.sidebar.text_input(
        "Folder with Monitor#.txt files",
        value=st.session_state.get("data_dir", ""),
        help="Path to a folder containing your Trikinetics Monitor<n>.txt files.",
    )
    st.session_state["data_dir"] = data_dir

if st.sidebar.button("Generate sample data", use_container_width=True):
    import make_sample_data
    sample_dir = os.path.join(HERE, "sample_data")
    make_sample_data.main(sample_dir)
    # sample data lives on the local disk, so switch to folder mode to read it.
    st.session_state["data_dir"] = sample_dir
    st.session_state["data_mode"] = "Local folder"
    st.rerun()

# resolve the effective data directory for whichever mode is active
effective_dir = ""
if data_mode == "Upload files" and uploads:
    tmp = tempfile.mkdtemp(prefix="dam_upload_")
    for uf in uploads:
        with open(os.path.join(tmp, uf.name), "wb") as fh:
            fh.write(uf.getbuffer())
    effective_dir = tmp
elif data_mode == "Local folder":
    effective_dir = data_dir

monitors_found = _list_monitors(effective_dir)
if monitors_found:
    st.sidebar.success("Found monitors: %s" %
                       ", ".join(str(m) for m in monitors_found))
elif effective_dir:
    st.sidebar.warning("No Monitor#.txt files found.")

st.sidebar.header("2. Global config")
env_monitors_str = st.sidebar.text_input(
    "Environmental monitor numbers", value=DEFAULT_ENV_MONITORS,
    help="Comma-separated list of monitor numbers that are DEnM (environmental) units.",
)
max_monitor = st.sidebar.number_input(
    "Max monitor number", min_value=1, max_value=999, value=120,
    help="Highest valid monitor index, used for error checking.",
)
try:
    env_monitors = [int(x.strip()) for x in env_monitors_str.split(",") if x.strip()]
except ValueError:
    env_monitors = []
    st.sidebar.error("Environmental monitors must be integers.")

st.sidebar.header("Import settings")
key_upload = st.sidebar.file_uploader("Load an experiment .ini", type="ini")
if key_upload is not None and st.sidebar.button("Apply loaded .ini"):
    tmp_ini = os.path.join(tempfile.mkdtemp(), "key.ini")
    with open(tmp_ini, "wb") as fh:
        fh.write(key_upload.getbuffer())
    protocol_dict, genotype_dict = file_io.read_key(tmp_ini)
    st.session_state["k_bin"] = protocol_dict["bin"]
    st.session_state["k_lon"] = protocol_dict["lights_on"].hour
    st.session_state["k_loff"] = protocol_dict["lights_off"].hour
    st.session_state["k_dd"] = protocol_dict["DD"]
    st.session_state["k_check"] = protocol_dict["check_day"]
    st.session_state["k_denm"] = protocol_dict["DEnM"]
    st.session_state["k_effector"] = protocol_dict["effector"]
    st.session_state["k_control"] = ", ".join(protocol_dict["control_genotype"])
    st.session_state["k_gender"] = protocol_dict["gender"]
    rows = []
    for name, positions in genotype_dict.items():
        for (m, first, last) in positions:
            rows.append({"Genotype": name, "Monitor": int(m),
                         "First channel": int(first), "Last channel": int(last)})
    st.session_state["genotype_df"] = pd.DataFrame(rows)
    st.rerun()

# --------------------------------------------------------------------------- #
# main: protocol + genotypes
# --------------------------------------------------------------------------- #
st.title("Drosophila Activity Analysis")
st.caption("Sleep & activity analysis for Trikinetics DAM/DEnM data — "
           "a Python 3 GUI for williamrowell/drosophila_activity_analysis.")

st.header("3. Protocol")
c1, c2, c3, c4 = st.columns(4)
bin_size = c1.number_input("Bin (minutes)", 1, 240, key="k_bin",
                           help="Time-bin width for plotting and Excel output.")
lights_on = c2.number_input("Lights on (hour)", 0, 23, key="k_lon")
lights_off = c3.number_input("Lights off (hour)", 0, 23, key="k_loff")
gender = c4.selectbox("Gender", ["f", "m", "x"], key="k_gender")

c5, c6, c7, c8 = st.columns(4)
DD = c5.number_input("DD start day", 0, 60, key="k_dd",
                     help="Day the constant-dark (DD) phase begins; loading date = 0. Use 0 for none.")
check_day = c6.number_input("Dead-fly check day", 0, 60, key="k_check",
                            help="Day used to detect dead flies; loading date = 0.")
# DEnM options track the env-monitor list. Prefer an environmental monitor
# that is actually present in the data folder so the default "just works".
denm_options = env_monitors or [26]
found_env = [m for m in monitors_found if m in env_monitors]
current_denm = st.session_state.get("k_denm")
if current_denm not in denm_options:
    current_denm = None
if found_env and current_denm not in found_env:
    st.session_state["k_denm"] = found_env[0]
elif current_denm is None:
    st.session_state["k_denm"] = denm_options[0]
denm = c7.selectbox("DEnM (environmental monitor)", denm_options, key="k_denm")
effector = c8.text_input("Effector", key="k_effector",
                         help="Label used on plots. Use a single underscore if none.")

control_genotype = st.text_input(
    "Control genotype(s)", key="k_control",
    help="Comma-separated genotype name(s) plotted as controls against each experimental line.",
)

st.header("4. Genotypes → monitor / channel positions")
st.caption("One row per (monitor, channel range). Repeat a genotype name across "
           "rows to span multiple monitors. Channels are 1–32.")
genotype_df = st.data_editor(
    st.session_state["genotype_df"],
    num_rows="dynamic", use_container_width=True, key="genotype_editor",
    column_config={
        "Genotype": st.column_config.TextColumn(required=True),
        "Monitor": st.column_config.NumberColumn(min_value=1, max_value=int(max_monitor), step=1),
        "First channel": st.column_config.NumberColumn(min_value=1, max_value=32, step=1),
        "Last channel": st.column_config.NumberColumn(min_value=1, max_value=32, step=1),
    },
)
st.session_state["genotype_df"] = genotype_df

protocol = {
    "bin": int(bin_size), "lights_on": int(lights_on), "lights_off": int(lights_off),
    "DD": int(DD), "check_day": int(check_day), "DEnM": int(denm),
    "effector": effector.strip() or "_",
    "control_genotype": control_genotype.strip() or "_", "gender": gender,
}

st.download_button(
    "⬇︎ Export settings as .ini",
    data=_build_ini(protocol, genotype_df),
    file_name="experiment.ini", mime="text/plain",
)

# --------------------------------------------------------------------------- #
# run
# --------------------------------------------------------------------------- #
st.header("5. Run")
run = st.button("▶︎ Run analysis", type="primary", use_container_width=True)

if run:
    problems = []
    if not effective_dir or not os.path.isdir(effective_dir):
        problems.append("Choose a valid data folder or upload monitor files.")
    if not env_monitors:
        problems.append("Set the environmental monitor list in the sidebar.")
    genotype_dict = _genotype_dict_from_df(genotype_df)
    if not genotype_dict:
        problems.append("Add at least one genotype row.")

    if problems:
        for p in problems:
            st.error(p)
    else:
        config_dict = {"env_monitors": env_monitors, "max_monitor": int(max_monitor)}
        out_dir = tempfile.mkdtemp(prefix="dam_out_")
        log_area = st.empty()
        logs = []

        def _log(msg):
            logs.append(msg)
            log_area.code("\n".join(logs))

        try:
            with st.spinner("Running analysis…"):
                result = pipeline.run_analysis(
                    config_dict, protocol, genotype_dict,
                    effective_dir, out_dir, basename="experiment", log=_log)
            st.session_state["result"] = result
            st.session_state["out_dir"] = out_dir
            st.success("Analysis complete.")
        except Exception as exc:  # surface pipeline errors in the UI
            st.session_state["result"] = None
            st.exception(exc)

# --------------------------------------------------------------------------- #
# results
# --------------------------------------------------------------------------- #
result = st.session_state.get("result")
out_dir = st.session_state.get("out_dir")

if result is not None:
    st.header("Results")

    if result.dead_flies:
        st.warning("Dead flies removed: " + ", ".join(result.dead_flies))
    else:
        st.info("No dead flies detected.")

    tab_env, tab_act, tab_sleep, tab_files = st.tabs(
        ["🌡 Environment", "🏃 Activity", "😴 Sleep", "📁 Downloads"])

    with tab_env:
        if result.metadata_figures:
            for i, fig in enumerate(result.metadata_figures, 1):
                st.pyplot(fig)
        else:
            st.write("No environment plots were generated.")

    with tab_act:
        if result.activity_figures:
            for genotype, figs in result.activity_figures.items():
                st.subheader(genotype)
                for fig in figs:
                    st.pyplot(fig)
        else:
            st.write("No activity plots (need at least one non-control genotype).")

    with tab_sleep:
        if result.sleep_figures:
            for genotype, figs in result.sleep_figures.items():
                st.subheader(genotype)
                for fig in figs:
                    st.pyplot(fig)
        else:
            st.write("No sleep plots (need at least one non-control genotype).")

    with tab_files:
        st.download_button(
            "⬇︎ Download all results (.zip)",
            data=_zip_output(out_dir),
            file_name="drosophila_results.zip", mime="application/zip",
            use_container_width=True,
        )
        st.divider()
        for path in result.output_files:
            if not os.path.isfile(path):
                continue
            with open(path, "rb") as fh:
                st.download_button("⬇︎ " + os.path.basename(path),
                                   data=fh.read(),
                                   file_name=os.path.basename(path),
                                   key="dl_" + os.path.basename(path))
