"""
Regression tests for the analysis pipeline.

These guard the behavior the GUI depends on, so future iterations that touch
the `dam` package fail loudly instead of silently changing results.

Run with:  pytest
"""

import os
import sys

import matplotlib
matplotlib.use("Agg")

import numpy as np
import pandas as pd
import pytest

# make the project root importable when pytest is run from anywhere
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

import make_sample_data
from dam import analyze, file_io, pipeline

CONFIG = {"env_monitors": [26], "max_monitor": 120}
PROTOCOL = {
    "bin": 30, "lights_on": 9, "lights_off": 21, "DD": 0, "check_day": 1,
    "DEnM": 26, "effector": "dTrpA1", "control_genotype": "control_GAL4",
    "gender": "f",
}
GENOTYPES = {
    "control_GAL4": [("1", "1", "16")],
    "experimental_line": [("1", "17", "32"), ("2", "1", "16")],
}


@pytest.fixture(scope="module")
def data_dir(tmp_path_factory):
    d = tmp_path_factory.mktemp("sample")
    make_sample_data.main(str(d))
    return str(d)


@pytest.fixture(scope="module")
def result(data_dir, tmp_path_factory):
    out = tmp_path_factory.mktemp("out")
    return pipeline.run_analysis(
        CONFIG, dict(PROTOCOL), {k: list(v) for k, v in GENOTYPES.items()},
        data_dir, str(out), basename="t")


# --- pure sleep logic -------------------------------------------------------
def test_sleep_needs_five_consecutive_zeros():
    # 4 zeros -> not sleep; 5 zeros -> sleep
    assert analyze._sleep_from_activity([1, 0, 0, 0, 0, 1]).sum() == 0
    assert list(analyze._sleep_from_activity([0, 0, 0, 0, 0])) == [1, 1, 1, 1, 1]


def test_sleep_run_extends_and_breaks():
    vals = [0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0]  # 6-zero run, then a short run
    sleep = analyze._sleep_from_activity(vals)
    assert list(sleep) == [1, 1, 1, 1, 1, 1, 0, 0, 0, 0, 0]


# --- end-to-end pipeline ----------------------------------------------------
def test_dead_fly_detected(result):
    assert "control_GAL4_M1C8" in result.dead_flies


def test_channel_counts(result):
    # control loses its one dead fly (16 -> 15); experimental spans 32 channels
    assert result.activity_dict["control_GAL4"].shape[1] == 15
    assert result.activity_dict["experimental_line"].shape[1] == 32


def test_figures_present(result):
    assert len(result.metadata_figures) == 2  # two full days in the sample
    assert result.activity_figures["experimental_line"]
    assert result.sleep_figures["experimental_line"]


def test_output_files_written(result):
    names = {os.path.basename(p) for p in result.output_files}
    assert "t_activity.xlsx" in names
    assert "t_sleep.xlsx" in names
    for path in result.output_files:
        assert os.path.isfile(path)


def test_excel_columns(result):
    xlsx = next(p for p in result.output_files if p.endswith("t_activity.xlsx"))
    df = pd.read_excel(xlsx)
    for col in ("date", "time", "control_GAL4_mean", "experimental_line_N"):
        assert col in df.columns
    assert (df["control_GAL4_N"] == 15).all()


def test_sleep_values_are_binary(result):
    sleep = result.sleep_dict["experimental_line"].to_numpy()
    assert set(np.unique(sleep)).issubset({0, 1})
