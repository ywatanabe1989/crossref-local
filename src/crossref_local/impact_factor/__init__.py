"""
Impact Factor calculation module.

Calculates journal impact factors from the local CrossRef database
by analyzing citation patterns.

Usage:
    >>> from crossref_local.impact_factor import ImpactFactorCalculator
    >>> with ImpactFactorCalculator() as calc:
    ...     result = calc.calculate_impact_factor("Nature", target_year=2023)
    ...     print(f"IF: {result['impact_factor']:.3f}")
"""

from .calculator import ImpactFactorCalculator
from .journal_lookup import JournalLookup

__all__ = [
    "ImpactFactorCalculator",
    "JournalLookup",
]
