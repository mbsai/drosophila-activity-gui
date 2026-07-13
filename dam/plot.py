"""
Plotting: build matplotlib figures for environment metadata and for
activity/sleep by genotype.

Unlike the original module (which wrote PDFs directly), each function here
returns a list of matplotlib Figures so the caller can preview them in a GUI
and/or save them. Use ``save_pdf`` to write a multi-page PDF.

Python 3 port of the original ``plot.py`` (William Rowell, 2014).
"""

import datetime as dt
import math

import matplotlib.dates as mpld
import numpy as np
import pandas as pd
from matplotlib.backends.backend_pdf import PdfPages
from matplotlib.figure import Figure

from . import analyze

COLOR_CYCLE = ['k', 'r', 'b', 'g', 'm', 'c']

_YLABELS = {
    'activity': ('beam crossings per %d minutes', (0, 100)),
    'sleep': ('minutes sleep per %d minutes', (0, 30)),
}
_GENDER_LABELS = {'f': r'$♀$', 'm': r'$♂$'}


def save_pdf(figures, path):
    """Write a list of figures to a multi-page PDF."""
    with PdfPages(path) as pdf:
        for fig in figures:
            pdf.savefig(fig)
    return path


def metadata(protocol_dict, DEnM_df):
    """
    One figure per full day showing light (lux), temperature (C) and relative
    humidity (%).
    """
    dates, start_date, end_date = analyze.calculate_dates(protocol_dict, DEnM_df)
    figures = []

    for day in range(1, len(dates)):
        start = start_date + dt.timedelta(days=(day - 1))
        end = start_date + dt.timedelta(days=day)
        if end > end_date:
            continue

        fig = Figure(figsize=(8, 6))
        ax = fig.subplots(3, sharex=True)

        L = DEnM_df['Lavg'].loc[start:end]
        T = DEnM_df['Tavg'].loc[start:end]
        H = DEnM_df['Havg'].loc[start:end]
        ax[0].plot(L.index, L.values, '-', color='k')
        ax[1].plot(T.index, T.values, '-', color='r')
        ax[2].plot(H.index, H.values, '-', color='b')

        ax[0].set_title('DEnM %s Day %d' % (protocol_dict['DEnM'], day))

        ax[0].set_ylabel('light (lux)')
        ax[0].set_ylim(0, 400)
        ax[0].yaxis.set_ticks(np.arange(0, 401, 100))

        ax[1].set_ylabel(u'temp ($^\\circ$C)')
        ax[1].set_ylim(18, 36)
        ax[1].yaxis.set_ticks(np.arange(18, 37, 5))

        ax[2].set_ylabel('rel hum (%)')
        ax[2].set_ylim(55, 75)
        ax[2].yaxis.set_ticks(np.arange(55, 76, 5))

        for a in ax:
            a.set_xlim(start, end)
            a.xaxis.grid(True, which='major')
        ax[2].xaxis.set_major_locator(mpld.HourLocator(interval=2))
        ax[2].xaxis.set_major_formatter(mpld.DateFormatter('%H'))
        ax[2].set_xlabel('time (h)')
        fig.subplots_adjust(hspace=0.1)
        figures.append(fig)

    return figures


def data(protocol_dict, DEnM_df, data_dict, genotype_list, data_type):
    """
    One figure per full day plotting the mean (+/- sem) of ``data_type``
    ('activity' or 'sleep') for every genotype in ``genotype_list``.
    """
    dates, start_date, end_date = analyze.calculate_dates(protocol_dict, DEnM_df)
    resample_freq = '%dmin' % protocol_dict['bin']

    t_index = DEnM_df.loc[start_date:end_date].resample(resample_freq).sum().index
    mean_df = pd.DataFrame(index=t_index)
    sem_df = pd.DataFrame(index=t_index)
    for genotype in genotype_list:
        binned = data_dict[genotype].loc[start_date:end_date].resample(resample_freq).sum()
        mean_df[genotype] = binned.mean(axis=1)
        sem_df[genotype] = binned.std(axis=1) / math.sqrt(binned.shape[1])

    ylabel, ylim = _YLABELS[data_type]
    ylabel = ylabel % protocol_dict['bin']
    light_bar = ylim[1]
    gender = _GENDER_LABELS.get(protocol_dict['gender'], '')

    figures = []
    for day in range(1, len(dates)):
        start = start_date + dt.timedelta(days=(day - 1))
        end = start_date + dt.timedelta(days=day)
        if end > end_date:
            continue

        fig = Figure(figsize=(8, 5))
        ax = fig.subplots()

        for gi, genotype in enumerate(genotype_list):
            color = COLOR_CYCLE[gi % len(COLOR_CYCLE)] if len(genotype_list) > 1 else 'r'
            seg_mean = mean_df.loc[start:end, genotype]
            seg_sem = sem_df.loc[start:end, genotype]
            label = '%s N=%d' % (genotype, data_dict[genotype].shape[1])
            ax.errorbar(seg_mean.index, seg_mean.values, yerr=seg_sem.values,
                        fmt='-', color=color, label=label,
                        elinewidth=0.6, capsize=0)

        mean_temp = round(DEnM_df['Tavg'].loc[start:end].mean(), 1)
        ax.set_title(u'%s x %s %s %s Day %d (%s$^\\circ$C)' % (
            genotype_list[-1], protocol_dict['effector'], gender,
            data_type, day, mean_temp))
        ax.xaxis.set_major_locator(mpld.HourLocator(interval=2))
        ax.xaxis.set_major_formatter(mpld.DateFormatter('%H'))
        ax.xaxis.grid(True, which='major')
        ax.set_xlabel('time (h)')
        ax.set_ylabel(ylabel)
        ax.set_ylim(ylim)
        ax.set_xlim(start, end)

        box = ax.get_position()
        ax.set_position([box.x0, box.y0 + box.height * 0.1,
                         box.width, box.height * 0.9])
        if len(genotype_list) > 1:
            ax.legend(loc='upper center', bbox_to_anchor=(0.5, -0.12),
                      ncol=2, prop={'size': 'x-small'})

        # dark bar marking the D phase
        if day < protocol_dict['DD']:
            ax.axhline(y=light_bar, xmin=0.5, xmax=1, linewidth=3, color='k')
        else:
            ax.axhline(y=light_bar, xmin=0, xmax=1, linewidth=3, color='k')

        figures.append(fig)

    return figures


if __name__ == '__main__':
    pass
