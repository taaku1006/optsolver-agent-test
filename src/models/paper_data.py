"""Models for paper data extracted from Stage 1."""

from typing import Any, Optional

from pydantic import BaseModel, Field


class PaperSection(BaseModel):
    """A section of the paper."""

    title: str = Field(
        ...,
        description="Title of the section"
    )
    content: str = Field(
        ...,
        description="Text content of the section"
    )
    page: Optional[int] = Field(
        None,
        description="Page number where the section starts"
    )
    subsections: list["PaperSection"] = Field(
        default_factory=list,
        description="Subsections within this section"
    )


class Table(BaseModel):
    """A table or figure from the paper."""

    id: str = Field(
        ...,
        description="Table/figure identifier (e.g., 'Table 1', 'Figure 3')"
    )
    caption: Optional[str] = Field(
        None,
        description="Caption or title of the table/figure"
    )
    content: Optional[str] = Field(
        None,
        description="Text representation of the table content"
    )
    data: Optional[dict[str, Any]] = Field(
        None,
        description="Structured data extracted from the table"
    )
    page: Optional[int] = Field(
        None,
        description="Page number where the table/figure appears"
    )


class Claim(BaseModel):
    """A claim made in the paper."""

    text: str = Field(
        ...,
        description="The claim text"
    )
    section: Optional[str] = Field(
        None,
        description="Section where the claim appears"
    )
    claim_type: Optional[str] = Field(
        None,
        description="Type of claim (e.g., 'main_contribution', 'result', 'comparison')"
    )
    supporting_evidence: list[str] = Field(
        default_factory=list,
        description="References to evidence supporting the claim"
    )


class Experiment(BaseModel):
    """An experiment or evaluation described in the paper."""

    name: Optional[str] = Field(
        None,
        description="Name or description of the experiment"
    )
    dataset: Optional[str] = Field(
        None,
        description="Dataset used in the experiment"
    )
    metrics: list[str] = Field(
        default_factory=list,
        description="Metrics used to evaluate the experiment"
    )
    baselines: list[str] = Field(
        default_factory=list,
        description="Baseline methods compared against"
    )
    results: Optional[dict[str, Any]] = Field(
        None,
        description="Experimental results"
    )


class Metadata(BaseModel):
    """Metadata about the paper."""

    title: Optional[str] = Field(
        None,
        description="Title of the paper"
    )
    authors: list[str] = Field(
        default_factory=list,
        description="List of authors"
    )
    year: Optional[int] = Field(
        None,
        description="Publication year"
    )
    venue: Optional[str] = Field(
        None,
        description="Publication venue (conference/journal)"
    )
    doi: Optional[str] = Field(
        None,
        description="Digital Object Identifier"
    )
    arxiv_id: Optional[str] = Field(
        None,
        description="arXiv identifier if applicable"
    )


class PaperData(BaseModel):
    """Structured data extracted from a paper by Stage 1.

    This model represents the output of Stage 1 (PDF text extraction
    and structure parsing) and serves as the input to Stage 2
    (logic and methodology verification).
    """

    metadata: Metadata = Field(
        default_factory=Metadata,
        description="Paper metadata (title, authors, year, etc.)"
    )
    abstract: Optional[str] = Field(
        None,
        description="Paper abstract"
    )
    sections: list[PaperSection] = Field(
        default_factory=list,
        description="Main sections of the paper"
    )
    tables: list[Table] = Field(
        default_factory=list,
        description="Tables and figures extracted from the paper"
    )
    claims: list[Claim] = Field(
        default_factory=list,
        description="Key claims made in the paper"
    )
    experiments: list[Experiment] = Field(
        default_factory=list,
        description="Experiments and evaluations described in the paper"
    )
    references: list[str] = Field(
        default_factory=list,
        description="Citations and references"
    )
    full_text: Optional[str] = Field(
        None,
        description="Complete text content of the paper"
    )

    class Config:
        """Pydantic model configuration."""

        json_schema_extra = {
            "example": {
                "metadata": {
                    "title": "AlphaOPT: Reinforcement Learning for Optimization",
                    "authors": ["John Doe", "Jane Smith"],
                    "year": 2023,
                    "venue": "NeurIPS"
                },
                "abstract": "We present AlphaOPT, a novel approach...",
                "sections": [
                    {
                        "title": "Introduction",
                        "content": "Optimization problems are ubiquitous...",
                        "page": 1
                    }
                ],
                "tables": [
                    {
                        "id": "Table 1",
                        "caption": "Comparison with baselines",
                        "content": "Method | Accuracy | Time\nAlphaOPT | 95% | 10s",
                        "page": 5
                    }
                ],
                "claims": [
                    {
                        "text": "AlphaOPT outperforms all baseline methods",
                        "section": "Results",
                        "claim_type": "main_contribution"
                    }
                ],
                "experiments": [
                    {
                        "name": "Benchmark evaluation",
                        "dataset": "TSP-100",
                        "metrics": ["accuracy", "runtime"],
                        "baselines": ["Greedy", "SA"]
                    }
                ]
            }
        }
