"""
Generate synthetic Trikinetics DAM/DEnM files so the GUI can be tried without
real data. Produces four full days of per-minute records.

    python make_sample_data.py [output_dir]

Creates in <output_dir> (default ./sample_data):
    Monitor26.txt   -- environmental monitor (DEnM)
    Monitor1.txt    -- activity monitor (DAM), 32 channels
    Monitor2.txt    -- activity monitor (DAM), 32 channels
    sample_experiment.ini -- a matching key file for the original CLI
"""

import datetime as dt
import os
import sys

import numpy as np

N_DAYS = 4
START_DATE = dt.date(2026, 7, 10)
LIGHTS_ON, LIGHTS_OFF = 9, 21   # hours
N_COLS = 42                     # Trikinetics rows have 42 tab-separated fields


def _timestamps():
    start = dt.datetime.combine(START_DATE, dt.time(0, 0, 0))
    minutes = N_DAYS * 24 * 60
    return [start + dt.timedelta(minutes=i) for i in range(minutes)]


def _row(sample_no, ts, fields):
    """Build one 42-field tab-separated line. fields maps col index -> value."""
    cols = ['0'] * N_COLS
    cols[0] = str(sample_no)
    cols[1] = ts.strftime('%d %b %y')
    cols[2] = ts.strftime('%H:%M:%S')
    cols[3] = '1'  # status OK
    for idx, val in fields.items():
        cols[idx] = str(val)
    return '\t'.join(cols)


def write_denm(path, timestamps, rng):
    lines = []
    for i, ts in enumerate(timestamps):
        lit = LIGHTS_ON <= ts.hour < LIGHTS_OFF
        lavg = int(rng.normal(300, 8)) if lit else int(abs(rng.normal(2, 1)))
        tavg = int(rng.normal(250, 3))          # tenths of a degree -> ~25.0 C
        havg = int(rng.normal(65, 1))           # relative humidity %
        lines.append(_row(i + 1, ts, {13: lavg, 18: tavg, 23: havg, 9: int(lit)}))
    with open(path, 'w') as fh:
        fh.write('\n'.join(lines) + '\n')


def write_dam(path, monitor, timestamps, rng, dead_channels=()):
    lines = []
    for i, ts in enumerate(timestamps):
        lit = LIGHTS_ON <= ts.hour < LIGHTS_OFF
        fields = {9: int(lit)}
        for ch in range(1, 33):
            col = 9 + ch  # channels occupy columns 10..41
            if ch in dead_channels:
                fields[col] = 0
                continue
            # daytime: active with occasional rests; night: mostly asleep
            if lit:
                count = int(rng.poisson(6)) if rng.random() > 0.25 else 0
            else:
                count = 0 if rng.random() > 0.12 else int(rng.poisson(3))
            fields[col] = count
        lines.append(_row(i + 1, ts, fields))
    with open(path, 'w') as fh:
        fh.write('\n'.join(lines) + '\n')


SAMPLE_INI = """\
[Protocol]
bin: 30
lights_on: 9
lights_off: 21
DD: 0
check_day: 1
DEnM: 26
effector: dTrpA1
control_genotype: control_GAL4
gender: f

[Genotypes]
control_GAL4: 1.1-16
experimental_line: 1.17-32, 2.1-16
"""


def main(out_dir='sample_data'):
    os.makedirs(out_dir, exist_ok=True)
    rng = np.random.default_rng(42)
    timestamps = _timestamps()

    write_denm(os.path.join(out_dir, 'Monitor26.txt'), timestamps, rng)
    # channel 8 on monitor 1 is a dead fly (all-zero activity)
    write_dam(os.path.join(out_dir, 'Monitor1.txt'), 1, timestamps, rng,
              dead_channels=(8,))
    write_dam(os.path.join(out_dir, 'Monitor2.txt'), 2, timestamps, rng)

    with open(os.path.join(out_dir, 'sample_experiment.ini'), 'w') as fh:
        fh.write(SAMPLE_INI)

    print('Wrote sample data to %s/' % out_dir)


if __name__ == '__main__':
    main(sys.argv[1] if len(sys.argv) > 1 else 'sample_data')
