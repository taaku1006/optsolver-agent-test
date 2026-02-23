"""Category checkers for methodological issue detection.

This package contains the base checker interface and implementations
for all 9 categories of methodological issues:
- claim_evidence_gap
- data_leakage
- unfair_comparison
- cherry_picking
- missing_ablation
- statistical_validity
- implicit_assumption
- reproducibility
- causal_overclaim
"""

from src.categories.base import BaseChecker

__all__ = ["BaseChecker"]
