"""Models for methodological issues detected in papers."""

from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field, field_validator


class Severity(str, Enum):
    """Severity level of a methodological issue."""

    CRITICAL = "critical"
    WARNING = "warning"
    INFO = "info"


class Evidence(BaseModel):
    """Evidence supporting a methodological issue."""

    section: Optional[str] = Field(
        None,
        description="Section of the paper where the issue was found"
    )
    quote: Optional[str] = Field(
        None,
        description="Direct quote from the paper demonstrating the issue"
    )
    table_reference: Optional[str] = Field(
        None,
        description="Reference to table or figure demonstrating the issue"
    )
    page: Optional[int] = Field(
        None,
        description="Page number where the issue appears"
    )


class MethodologicalIssue(BaseModel):
    """A methodological issue detected in a paper.

    Represents one of the 9 categories of issues that the logic checker
    can detect: claim_evidence_gap, data_leakage, unfair_comparison,
    cherry_picking, missing_ablation, statistical_validity,
    implicit_assumption, reproducibility, or causal_overclaim.
    """

    category: str = Field(
        ...,
        description="Category of the methodological issue"
    )
    severity: Severity = Field(
        ...,
        description="Severity level: critical, warning, or info"
    )
    confidence: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Confidence score between 0 and 1"
    )
    title: str = Field(
        ...,
        description="Short title describing the issue"
    )
    description: str = Field(
        ...,
        description="Detailed description of the methodological issue"
    )
    evidence: Evidence = Field(
        ...,
        description="Evidence supporting this issue (section, quote, or table reference)"
    )
    suggestions: list[str] = Field(
        default_factory=list,
        description="Actionable suggestions for how to address the issue"
    )

    @field_validator("category")
    @classmethod
    def validate_category(cls, v: str) -> str:
        """Validate that the category is one of the 9 supported categories."""
        valid_categories = {
            "claim_evidence_gap",
            "data_leakage",
            "unfair_comparison",
            "cherry_picking",
            "missing_ablation",
            "statistical_validity",
            "implicit_assumption",
            "reproducibility",
            "causal_overclaim",
        }
        if v not in valid_categories:
            raise ValueError(
                f"Invalid category '{v}'. Must be one of: {', '.join(sorted(valid_categories))}"
            )
        return v

    @field_validator("confidence")
    @classmethod
    def validate_confidence(cls, v: float) -> float:
        """Validate that confidence is between 0 and 1."""
        if not 0.0 <= v <= 1.0:
            raise ValueError(f"Confidence must be between 0 and 1, got {v}")
        return v

    class Config:
        """Pydantic model configuration."""

        json_schema_extra = {
            "example": {
                "category": "unfair_comparison",
                "severity": "critical",
                "confidence": 0.85,
                "title": "Unfair baseline comparison",
                "description": "The paper compares against outdated baselines without using the current state-of-the-art methods.",
                "evidence": {
                    "section": "Experimental Results",
                    "quote": "We compare our method against baseline X from 2015...",
                    "table_reference": "Table 2"
                },
                "suggestions": [
                    "Include comparison with current state-of-the-art methods from 2023-2024",
                    "Justify the choice of baselines if older methods are used",
                    "Acknowledge the limitations of the comparison"
                ]
            }
        }
