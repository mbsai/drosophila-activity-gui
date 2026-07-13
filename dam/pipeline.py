"""
Orchestrate a full analysis run from plain Python dicts.

This is the Python 3 / GUI-friendly equivalent of the original
``process_experiment.py`` ``main()``: instead of parsing ini files and reading
``sys.argv``, it takes already-parsed dicts plus a data directory and an output
directory, runs the whole pipeline, and returns a structured result.
"""

import os

from . import analyze, file_io, plot


class AnalysisResult:
    """Container for everything produced by a run."""

    def __init__(self):
        self.dead_flies = []
        self.metadata_figures = []
        self.activity_figures = {}   # genotype -> [Figure, ...]
        self.sleep_figures = {}      # genotype -> [Figure, ...]
        self.output_files = []       # list of written file paths
        self.activity_dict = {}
        self.sleep_dict = {}
        self.log_lines = []


def run_analysis(config_dict, protocol_dict, genotype_dict,
                 data_dir, out_dir, basename='experiment', log=None):
    """
    Run the complete activity/sleep analysis.

    config_dict   : {'env_monitors': [...], 'max_monitor': int}
    protocol_dict : normalized protocol parameters (see file_io.normalize_protocol)
    genotype_dict : {genotype: [(monitor, first, last), ...]}
    data_dir      : folder containing Monitor<n>.txt files
    out_dir       : folder to write outputs into (created if needed)
    basename      : stem used for output file names
    log           : optional callable(str) for progress messages

    Returns an AnalysisResult.
    """
    result = AnalysisResult()

    def _log(msg):
        result.log_lines.append(str(msg))
        if log is not None:
            log(str(msg))

    os.makedirs(out_dir, exist_ok=True)

    # protocol_dict may arrive raw (from a GUI); normalize defensively.
    protocol_dict = file_io.normalize_protocol(protocol_dict)

    _log('Reading environmental monitor %s...' % protocol_dict['DEnM'])
    DEnM_df = file_io.read_DEnM_data(
        protocol_dict['DEnM'], config_dict['env_monitors'], data_dir, log=_log)

    dam_monitors = sorted({int(pos[0])
                           for positions in genotype_dict.values()
                           for pos in positions})
    _log('Reading activity monitors: %s' % ', '.join(map(str, dam_monitors)))
    DAM_dict = {
        'M%d' % m: file_io.read_DAM_data(m, config_dict['max_monitor'], data_dir)
        for m in dam_monitors
    }

    _log('Aggregating activity by genotype...')
    activity_dict = analyze.aggregate_by_genotype(
        genotype_dict, config_dict, DEnM_df, DAM_dict)

    _log('Checking for dead flies (day %d)...' % protocol_dict['check_day'])
    result.dead_flies = analyze.mark_dead_flies(
        protocol_dict, DEnM_df, activity_dict, genotype_dict, log=_log)

    _log('Calculating sleep...')
    sleep_dict = analyze.calculate_sleep(activity_dict)

    result.activity_dict = activity_dict
    result.sleep_dict = sleep_dict

    # --- environment metadata plot ---
    _log('Plotting environment metadata...')
    result.metadata_figures = plot.metadata(protocol_dict, DEnM_df)
    if result.metadata_figures:
        pdf_path = os.path.join(out_dir, 'DEnM_%s.pdf' % protocol_dict['DEnM'])
        plot.save_pdf(result.metadata_figures, pdf_path)
        result.output_files.append(pdf_path)

    # --- per-genotype activity/sleep plots (each experimental line vs controls) ---
    controls = []
    if set(protocol_dict['control_genotype']) & set(genotype_dict.keys()):
        controls = list(protocol_dict['control_genotype'])

    for genotype in genotype_dict.keys():
        if genotype in protocol_dict['control_genotype']:
            continue
        genotype_list = controls + [genotype]

        _log('Plotting activity/sleep for %s...' % genotype)
        act_figs = plot.data(protocol_dict, DEnM_df, activity_dict,
                             genotype_list, 'activity')
        slp_figs = plot.data(protocol_dict, DEnM_df, sleep_dict,
                            genotype_list, 'sleep')
        result.activity_figures[genotype] = act_figs
        result.sleep_figures[genotype] = slp_figs

        stem = '%s_%s_%s' % (genotype, protocol_dict['effector'],
                             protocol_dict['gender'])
        for figs, kind in ((act_figs, 'activity'), (slp_figs, 'sleep')):
            if figs:
                path = os.path.join(out_dir, '%s_%s.pdf' % (stem, kind))
                plot.save_pdf(figs, path)
                result.output_files.append(path)

    # --- excel output ---
    _log('Writing Excel output...')
    act_xlsx = os.path.join(out_dir, '%s_activity.xlsx' % basename)
    slp_xlsx = os.path.join(out_dir, '%s_sleep.xlsx' % basename)
    file_io.write_data(protocol_dict, DEnM_df, activity_dict, act_xlsx)
    file_io.write_data(protocol_dict, DEnM_df, sleep_dict, slp_xlsx)
    result.output_files.extend([act_xlsx, slp_xlsx])

    # --- dead flies text file ---
    dead_path = os.path.join(out_dir, '%s_dead_flies.txt' % basename)
    with open(dead_path, 'w') as fh:
        fh.write('\n'.join(result.dead_flies))
    result.output_files.append(dead_path)

    _log('Done.')
    return result


if __name__ == '__main__':
    pass
