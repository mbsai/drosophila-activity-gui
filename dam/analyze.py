"""
Analysis routines: aggregate activity by genotype, flag dead flies, and
compute sleep.

Python 3 port of the original ``analyze.py`` (William Rowell, 2014).
"""

import datetime as dt

import numpy as np
import pandas as pd


def aggregate_by_genotype(genotype_dict, config_dict, DEnM_df, DAM_dict):
    """
    Build a dict mapping each genotype to a datetime-indexed DataFrame whose
    columns are the activity channels belonging to that genotype.

    genotype_dict : {genotype: [(monitor, first_channel, last_channel), ...]}
    config_dict   : configuration values (needs 'max_monitor')
    DEnM_df       : environmental monitor DataFrame (supplies the time index)
    DAM_dict      : {'M<monitor>': activity DataFrame}
    """
    activity = dict()
    # Align everything to the environmental monitor's time index.
    time_series = DEnM_df.index

    for genotype, positions in genotype_dict.items():
        for (monitor, first, last) in positions:
            monitor = str(int(monitor))
            first, last = int(first), int(last)

            assert 1 <= int(monitor) <= config_dict['max_monitor'], \
                '%s is not a valid monitor number.' % monitor
            assert 1 <= first <= 32, \
                'First channel %s is out of range [1,32].' % first
            assert 1 <= last <= 32, \
                'Last channel %s is out of range [1,32].' % last
            assert first <= last, \
                'Last channel %s is less than first channel %s.' % (last, first)

            channels = ['M' + monitor + 'C' + str(c)
                        for c in range(first, last + 1)]
            dam = DAM_dict['M' + monitor]
            # reindex to the DEnM time base so activity/env stay aligned even
            # if the files differ by a stray minute at the edges.
            channels_df = dam.reindex(time_series)[channels]

            if genotype not in activity:
                activity[genotype] = channels_df.copy()
            else:
                activity[genotype] = activity[genotype].join(channels_df)

    return activity


def calculate_dates(protocol_dict, DEnM_df):
    """
    Return (dates, start_datetime, end_datetime).

    dates          : ordered list of calendar dates present in the data
    start_datetime : first full-day lights_on event (second calendar date)
    end_datetime   : last lights_off event that falls within the recording
    """
    dates = sorted(set(DEnM_df.index.map(lambda ts: ts.date())))
    start_date = dt.datetime.combine(dates[1], protocol_dict['lights_on'])
    end_date = dt.datetime.combine(dates[-1], protocol_dict['lights_off'])
    if end_date > DEnM_df.index[-1].to_pydatetime():
        end_date = dt.datetime.combine(dates[-2], protocol_dict['lights_off'])
    return dates, start_date, end_date


def mark_dead_flies(protocol_dict, DEnM_df, activity_dict, genotype_dict, log=print):
    """
    Detect flies with no activity for the entire 24h period following lights_on
    on ``check_day`` and drop their channels from ``activity_dict`` (mutates it).

    Returns a list of dead-fly labels formatted 'genotype_channel'.
    """
    dates, _, _ = calculate_dates(protocol_dict, DEnM_df)
    check_day = protocol_dict['check_day']

    if not (0 <= check_day < len(dates)):
        log(
            "WARNING: check_day is outside the range of available data; "
            "dead-fly detection has been disabled."
        )
        return []

    check_start = dt.datetime.combine(dates[check_day],
                                      protocol_dict['lights_on']) \
        + dt.timedelta(minutes=1)
    check_end = check_start + dt.timedelta(days=1)

    dead_flies = []
    for genotype in list(activity_dict.keys()):
        df = activity_dict[genotype]
        dead_channels = []
        for channel in list(df.columns):
            window = set(df.loc[check_start:check_end, channel].dropna())
            window.discard(0)
            if not window:
                log('%s:%s - dead' % (genotype, channel))
                dead_flies.append('_'.join([genotype, channel]))
                dead_channels.append(channel)
        if dead_channels:
            activity_dict[genotype] = df.drop(columns=dead_channels)
        # if every fly of this genotype is dead, drop the genotype entirely
        if activity_dict[genotype].shape[1] == 0:
            log('All flies of genotype %s are dead.' % genotype)
            del activity_dict[genotype]
            if genotype in genotype_dict:
                del genotype_dict[genotype]

    return dead_flies


def _sleep_from_activity(values, min_run=5):
    """
    Given a 1-D array of per-minute beam-crossing counts, return an int array
    marking sleep (1) where there is a run of ``min_run`` or more consecutive
    minutes of zero activity.
    """
    values = np.asarray(values)
    n = values.size
    sleep = np.zeros(n, dtype=int)

    i = 0
    while i < n:
        if values[i] != 0 or np.isnan(values[i]):
            i += 1
            continue
        j = i
        while j < n and values[j] == 0:
            j += 1
        if (j - i) >= min_run:
            sleep[i:j] = 1
        i = j
    return sleep


def calculate_sleep(activity_dict):
    """
    Return a dict of sleep DataFrames (1 = asleep) matching the structure of
    ``activity_dict``. Sleep is 5+ consecutive minutes without beam crossings.
    """
    sleep_dict = dict()
    for genotype, df in activity_dict.items():
        sleep = pd.DataFrame(index=df.index)
        for channel in df.columns:
            sleep[channel] = _sleep_from_activity(df[channel].to_numpy())
        sleep_dict[genotype] = sleep
    return sleep_dict


if __name__ == '__main__':
    pass
