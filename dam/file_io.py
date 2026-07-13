"""
File I/O: read config/key files and DAM/DEnM data files, and write aggregated
activity/sleep data to Excel.

Python 3 port of the original ``file_io.py`` (William Rowell, 2014).
"""

import configparser
import datetime as dt
import math
import os.path
import re

import numpy as np
import pandas as pd

from . import analyze

# status values that indicate bad data
BAD_STATUS = {50, 51, 52, 53, 55}


# --------------------------------------------------------------------------- #
# config / key parsing
# --------------------------------------------------------------------------- #
def _parse_section(config, section):
    """Return a section as a dict, coercing values to int where possible."""
    out = dict()
    for option in config.options(section):
        try:
            out[option] = config.getint(section, option)
        except ValueError:
            out[option] = config.get(section, option)
        assert out[option] != '', '%s is required, but not set.' % option
    return out


def read_config(configfile):
    """
    Load global configuration (env_monitors, max_monitor) from an ini file.
    """
    assert os.path.isfile(configfile), '%s does not exist.' % configfile

    config = configparser.ConfigParser()
    config.optionxform = str  # preserve case of keys
    config.read(configfile)

    config_dict = _parse_section(config, 'Config')
    config_dict['env_monitors'] = _parse_env_monitors(config_dict['env_monitors'])
    return config_dict


def _parse_env_monitors(value):
    """Normalize env_monitors into a list of ints."""
    if isinstance(value, int):
        return [value]
    return [int(x.strip()) for x in str(value).split(',') if x.strip()]


def read_key(keyfile):
    """
    Load protocol parameters and genotype/position mappings from an ini file.

    Returns (protocol_dict, genotype_dict).
    """
    assert os.path.isfile(keyfile), '%s does not exist.' % keyfile

    config = configparser.ConfigParser()
    config.optionxform = str
    config.read(keyfile)

    protocol_dict = _parse_section(config, 'Protocol')
    protocol_dict = normalize_protocol(protocol_dict)

    genotype_dict = dict()
    for genotype in config.options('Genotypes'):
        pos_string = config.get('Genotypes', genotype)
        genotype_dict.setdefault(genotype, []).extend(parse_positions(pos_string))

    return protocol_dict, genotype_dict


def normalize_protocol(protocol_dict):
    """
    Validate protocol values and convert lights_on/off to datetime.time and
    control_genotype to a list. Accepts int hours or datetime.time for lights.
    """
    protocol_dict = dict(protocol_dict)

    for key in ('lights_on', 'lights_off'):
        val = protocol_dict[key]
        if isinstance(val, dt.time):
            continue
        val = int(val)
        assert 0 <= val < 24, '%s must be between 0 and 23.' % key
        protocol_dict[key] = dt.time(val, 0, 0)

    if isinstance(protocol_dict.get('control_genotype'), str):
        protocol_dict['control_genotype'] = \
            [x.strip() for x in protocol_dict['control_genotype'].split(',') if x.strip()]

    assert int(protocol_dict['DD']) >= 0, 'DD must be a non-negative integer.'
    assert int(protocol_dict['check_day']) >= 0, \
        'check_day must be a non-negative integer.'
    assert protocol_dict['gender'] in ('m', 'f', 'x'), \
        'gender must be one of [m, f, x].'

    protocol_dict['DD'] = int(protocol_dict['DD'])
    protocol_dict['check_day'] = int(protocol_dict['check_day'])
    protocol_dict['DEnM'] = int(protocol_dict['DEnM'])
    protocol_dict['bin'] = int(protocol_dict['bin'])
    return protocol_dict


def parse_positions(pos_string):
    """
    Parse 'Mon.ChanLo-ChanHi, Mon.ChanLo-ChanHi' into a list of
    (monitor, first, last) string tuples.
    """
    pos_regex = re.compile(r'(\d{1,3})\.(\d{1,2})-(\d{1,2})')
    positions = []
    for item in pos_string.split(','):
        item = item.strip()
        if not item:
            continue
        match = pos_regex.match(item)
        assert match is not None, 'Could not parse position "%s".' % item
        positions.append(match.groups())
    return positions


# --------------------------------------------------------------------------- #
# monitor data files
# --------------------------------------------------------------------------- #
def _read_monitor_file(monitor_number, data_dir):
    datafile = os.path.join(data_dir, 'Monitor%s.txt' % monitor_number)
    assert os.path.isfile(datafile), \
        'Data file for monitor %s does not exist (%s).' % (monitor_number, datafile)
    return pd.read_csv(datafile, sep='\t', header=None)


def _build_datetime_index(df):
    """Combine the date (col 1) and time (col 2) columns into a datetime index."""
    stamps = df[1].astype(str).str.strip() + ' ' + df[2].astype(str).str.strip()
    return pd.to_datetime(stamps, format='%d %b %y %H:%M:%S')


def read_DEnM_data(monitor_number, ENV_MONITORS, data_dir='.', log=print):
    """
    Read a Drosophila Environmental Monitor file and return a datetime-indexed
    DataFrame with status, Lavg, Tavg, Havg and a boolean 'light' column.
    """
    assert int(monitor_number) in ENV_MONITORS, \
        'Monitor %s is not a known DEnM.' % monitor_number

    raw = _read_monitor_file(monitor_number, data_dir)
    # column positions (0-based): 3=status, 13=Lavg, 18=Tavg, 23=Havg
    df = raw[[3, 13, 18, 23]].copy()
    df.columns = ['status', 'Lavg', 'Tavg', 'Havg']
    df.index = _build_datetime_index(raw)

    if bad_status(df):
        log(
            "WARNING: DEnM contains timepoints with status errors; light, "
            "temperature, and humidity for those timepoints may be unreliable."
        )

    df['light'] = df['Lavg'] > 100
    df['Tavg'] = df['Tavg'].replace(0, np.nan) / 10.0
    df['Havg'] = df['Havg'].replace(0, np.nan)
    return df


def read_DAM_data(monitor_number, MAX_MONITOR, data_dir='.'):
    """
    Read a Drosophila Activity Monitor file and return a datetime-indexed
    DataFrame with status, Lstatus and 32 activity channels (M<n>C<1..32>).
    """
    assert 1 <= int(monitor_number) <= MAX_MONITOR, \
        '%s is not a valid monitor number.' % monitor_number

    raw = _read_monitor_file(monitor_number, data_dir)
    # column positions (0-based): 3=status, 9=Lstatus, 10..41=channels 1..32
    cols = [3, 9] + list(range(10, 42))
    df = raw[cols].copy()
    m = str(int(monitor_number))
    df.columns = ['M%sstatus' % m, 'M%sLstatus' % m] + \
        ['M%sC%d' % (int(m), c) for c in range(1, 33)]
    df.index = _build_datetime_index(raw)
    return df


def bad_status(df):
    """True if the DataFrame's status column contains any BAD_STATUS value."""
    return bool(set(df['status'].values) & BAD_STATUS)


# --------------------------------------------------------------------------- #
# output
# --------------------------------------------------------------------------- #
def write_data(protocol_dict, DEnM_df, data_dict, outname):
    """
    Write per-genotype mean / sem / N (binned) to an Excel file.
    """
    _, start_date, end_date = analyze.calculate_dates(protocol_dict, DEnM_df)
    resample_freq = '%dmin' % protocol_dict['bin']

    t_index = DEnM_df.loc[start_date:end_date].resample(resample_freq).sum().index
    output_df = pd.DataFrame(index=t_index)
    output_df['date'] = [i.strftime('%Y-%m-%d') for i in output_df.index]
    output_df['time'] = [i.strftime('%H:%M:%S') for i in output_df.index]

    for genotype, data in data_dict.items():
        binned = data.loc[start_date:end_date].resample(resample_freq).sum()
        output_df[genotype + '_mean'] = binned.mean(axis=1)
        output_df[genotype + '_sem'] = binned.std(axis=1) / math.sqrt(binned.shape[1])
        output_df[genotype + '_N'] = binned.shape[1]

    output_df.to_excel(outname, engine='openpyxl')
    return outname


if __name__ == '__main__':
    pass
