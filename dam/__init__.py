"""
Drosophila activity analysis (Python 3 port).

A modern port of William Rowell's `drosophila_activity_analysis` toolkit for
Trikinetics DAM/DEnM data, refactored into an importable package so it can be
driven from a GUI as well as the command line.

Modules
-------
file_io   : read config/key files and DAM/DEnM data; write Excel output.
analyze   : aggregate activity by genotype, flag dead flies, compute sleep.
plot      : build matplotlib figures for environment metadata and activity/sleep.
pipeline  : orchestrate a full analysis run from plain Python dicts.
"""

from . import analyze, file_io, plot, pipeline  # noqa: F401

__all__ = ["analyze", "file_io", "plot", "pipeline"]
