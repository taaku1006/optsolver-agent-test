"""Data models for the Logic & Methodology Verification pipeline."""

from .issue import Evidence, MethodologicalIssue, Severity
from .paper_data import (
    Claim,
    Experiment,
    Metadata,
    PaperData,
    PaperSection,
    Table,
)

__all__ = [
    # Issue models
    "Severity",
    "Evidence",
    "MethodologicalIssue",
    # Paper data models
    "PaperData",
    "PaperSection",
    "Table",
    "Claim",
    "Experiment",
    "Metadata",
]
