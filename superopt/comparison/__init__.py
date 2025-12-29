"""Comparison framework for evaluating SuperOpt against GEPA and ACE."""

from superopt.comparison.ace_comparison import ACEComparison
from superopt.comparison.framework import ComparisonFramework
from superopt.comparison.gepa_comparison import GEPAComparison

__all__ = ["GEPAComparison", "ACEComparison", "ComparisonFramework"]
