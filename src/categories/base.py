"""Base category checker interface.

All category-specific checkers inherit from BaseChecker and implement
the check() method to analyze paper data for a specific type of
methodological issue.
"""

from abc import ABC, abstractmethod
from typing import Optional

from src.models.issue import MethodologicalIssue
from src.models.paper_data import PaperData


class BaseChecker(ABC):
    """Abstract base class for category checkers.

    Each category checker examines paper data for a specific type of
    methodological issue (e.g., data leakage, unfair comparison) and
    returns a list of detected issues with evidence and suggestions.

    Subclasses must implement the check() method.

    Example:
        >>> class DataLeakageChecker(BaseChecker):
        ...     def __init__(self, claude_client):
        ...         super().__init__(claude_client)
        ...         self.category = "data_leakage"
        ...
        ...     def check(self, paper_data):
        ...         # Implementation here
        ...         return issues
    """

    def __init__(self, claude_client, category: Optional[str] = None):
        """Initialize the category checker.

        Args:
            claude_client: ClaudeClient instance for API calls
            category: Category name (e.g., "data_leakage"). If None,
                     subclass must set self.category in __init__
        """
        self.claude_client = claude_client
        self.category = category

    @abstractmethod
    def check(self, paper_data: PaperData) -> list[MethodologicalIssue]:
        """Check paper data for methodological issues in this category.

        Args:
            paper_data: Structured paper data from Stage 1 extraction

        Returns:
            List of MethodologicalIssue objects detected in this category.
            Returns empty list if no issues found.

        Raises:
            ClaudeClientError: If API call fails and fallback is not available
            ValueError: If paper_data is invalid or missing required fields
        """
        pass

    def _format_paper_data(self, paper_data: PaperData) -> str:
        """Format paper data for Claude API prompt.

        Args:
            paper_data: Structured paper data

        Returns:
            Formatted string representation of paper data
        """
        sections_text = "\n\n".join(
            f"## {section.title}\n{section.content}"
            for section in paper_data.sections
        )

        tables_text = "\n\n".join(
            f"### {table.id}: {table.caption or 'No caption'}\n{table.content or 'No content'}"
            for table in paper_data.tables
        )

        claims_text = "\n".join(
            f"- {claim.text} (Section: {claim.section or 'Unknown'})"
            for claim in paper_data.claims
        )

        experiments_text = "\n".join(
            f"- {exp.name or 'Unnamed'}: Dataset={exp.dataset}, Metrics={', '.join(exp.metrics)}, Baselines={', '.join(exp.baselines)}"
            for exp in paper_data.experiments
        )

        return f"""
**Title:** {paper_data.metadata.title or 'Unknown'}
**Authors:** {', '.join(paper_data.metadata.authors) if paper_data.metadata.authors else 'Unknown'}
**Year:** {paper_data.metadata.year or 'Unknown'}

**Abstract:**
{paper_data.abstract or 'No abstract available'}

**Sections:**
{sections_text or 'No sections available'}

**Tables and Figures:**
{tables_text or 'No tables available'}

**Claims:**
{claims_text or 'No claims available'}

**Experiments:**
{experiments_text or 'No experiments available'}
""".strip()

    def __repr__(self) -> str:
        """String representation of the checker."""
        return f"{self.__class__.__name__}(category='{self.category}')"
