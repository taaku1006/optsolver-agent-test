"""Logic checker orchestrator for methodological issue detection.

Coordinates all 9 category checkers to analyze paper data for methodological
issues in parallel, with graceful fallback for partial failures.
"""

import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Optional

from src.categories.causal_overclaim import CausalOverclaimChecker
from src.categories.cherry_picking import CherryPickingChecker
from src.categories.claim_evidence_gap import ClaimEvidenceGapChecker
from src.categories.data_leakage import DataLeakageChecker
from src.categories.implicit_assumption import ImplicitAssumptionChecker
from src.categories.missing_ablation import MissingAblationChecker
from src.categories.reproducibility import ReproducibilityChecker
from src.categories.statistical_validity import StatisticalValidityChecker
from src.categories.unfair_comparison import UnfairComparisonChecker
from src.claude_client import ClaudeClient
from src.models.issue import MethodologicalIssue
from src.models.paper_data import PaperData

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class LogicCheckerResult:
    """Result from logic checker analysis.

    Contains all detected issues and metadata about the analysis,
    including which categories succeeded or failed.
    """

    def __init__(
        self,
        issues: list[MethodologicalIssue],
        total_categories: int,
        successful_categories: int,
        failed_categories: list[str],
    ):
        """Initialize result.

        Args:
            issues: All detected methodological issues
            total_categories: Total number of categories checked
            successful_categories: Number of categories that completed successfully
            failed_categories: List of category names that failed
        """
        self.issues = issues
        self.total_categories = total_categories
        self.successful_categories = successful_categories
        self.failed_categories = failed_categories

    @property
    def is_partial(self) -> bool:
        """Whether this is a partial result due to some categories failing."""
        return len(self.failed_categories) > 0

    @property
    def success_rate(self) -> float:
        """Fraction of categories that completed successfully (0-1)."""
        if self.total_categories == 0:
            return 0.0
        return self.successful_categories / self.total_categories

    def to_dict(self) -> dict:
        """Convert result to dictionary for JSON serialization."""
        return {
            "issues": [issue.model_dump() for issue in self.issues],
            "metadata": {
                "total_categories": self.total_categories,
                "successful_categories": self.successful_categories,
                "failed_categories": self.failed_categories,
                "is_partial": self.is_partial,
                "success_rate": self.success_rate,
            }
        }


class LogicChecker:
    """Main orchestrator for methodological issue detection.

    Coordinates all 9 category checkers to analyze paper data in parallel,
    aggregating results and handling partial failures gracefully.

    The 9 categories are:
    1. claim_evidence_gap - Claims lacking supporting evidence
    2. data_leakage - Test data contaminating training
    3. unfair_comparison - Misleading baseline comparisons
    4. cherry_picking - Selective reporting of results
    5. missing_ablation - Insufficient validation of design choices
    6. statistical_validity - Missing significance tests
    7. implicit_assumption - Unstated assumptions
    8. reproducibility - Missing implementation details
    9. causal_overclaim - Causal claims without proper design

    Example:
        >>> client = ClaudeClient()
        >>> checker = LogicChecker(client)
        >>> result = checker.check(paper_data)
        >>> print(f"Found {len(result.issues)} issues")
        >>> print(f"Success rate: {result.success_rate:.1%}")
    """

    def __init__(
        self,
        claude_client: ClaudeClient,
        max_workers: Optional[int] = None,
        enable_parallel: bool = True,
    ):
        """Initialize logic checker.

        Args:
            claude_client: Claude API client for category checkers
            max_workers: Maximum number of parallel workers. Defaults to min(9, cpu_count + 4)
            enable_parallel: Whether to run category checks in parallel. Set to False for debugging.
        """
        self.claude_client = claude_client
        self.max_workers = max_workers
        self.enable_parallel = enable_parallel

        # Initialize all category checkers
        self.checkers = {
            "claim_evidence_gap": ClaimEvidenceGapChecker(claude_client),
            "data_leakage": DataLeakageChecker(claude_client),
            "unfair_comparison": UnfairComparisonChecker(claude_client),
            "cherry_picking": CherryPickingChecker(claude_client),
            "missing_ablation": MissingAblationChecker(claude_client),
            "statistical_validity": StatisticalValidityChecker(claude_client),
            "implicit_assumption": ImplicitAssumptionChecker(claude_client),
            "reproducibility": ReproducibilityChecker(claude_client),
            "causal_overclaim": CausalOverclaimChecker(claude_client),
        }

        logger.info(f"Initialized LogicChecker with {len(self.checkers)} category checkers")

    def check(self, paper_data: PaperData) -> LogicCheckerResult:
        """Check paper data for all methodological issues.

        Runs all 9 category checkers in parallel and aggregates results.
        Handles partial failures gracefully - if some categories fail,
        returns results from successful categories.

        Args:
            paper_data: Structured paper data from Stage 1 extraction

        Returns:
            LogicCheckerResult containing all detected issues and metadata

        Raises:
            ValueError: If paper_data is invalid or all categories fail
        """
        if not paper_data:
            raise ValueError("paper_data cannot be None")

        logger.info(f"Starting logic check for paper: {paper_data.metadata.title or 'Unknown'}")

        if self.enable_parallel:
            return self._check_parallel(paper_data)
        else:
            return self._check_sequential(paper_data)

    def _check_parallel(self, paper_data: PaperData) -> LogicCheckerResult:
        """Run category checks in parallel.

        Args:
            paper_data: Structured paper data

        Returns:
            LogicCheckerResult with aggregated issues
        """
        all_issues = []
        failed_categories = []
        successful_count = 0

        # Create a mapping of futures to category names
        future_to_category = {}

        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            # Submit all category checks
            for category_name, checker in self.checkers.items():
                future = executor.submit(self._run_category_check, category_name, checker, paper_data)
                future_to_category[future] = category_name

            # Collect results as they complete
            for future in as_completed(future_to_category):
                category_name = future_to_category[future]
                try:
                    issues = future.result()
                    successful_count += 1
                    all_issues.extend(issues)
                    logger.info(f"✓ {category_name}: Found {len(issues)} issues")
                except Exception as e:
                    failed_categories.append(category_name)
                    logger.warning(f"✗ {category_name}: Failed with error: {str(e)}")

        # Validate that at least some categories succeeded
        if successful_count == 0:
            raise ValueError(
                f"All {len(self.checkers)} category checks failed. "
                f"Failed categories: {', '.join(failed_categories)}"
            )

        logger.info(
            f"Logic check complete: {successful_count}/{len(self.checkers)} categories succeeded, "
            f"found {len(all_issues)} total issues"
        )

        return LogicCheckerResult(
            issues=all_issues,
            total_categories=len(self.checkers),
            successful_categories=successful_count,
            failed_categories=failed_categories,
        )

    def _check_sequential(self, paper_data: PaperData) -> LogicCheckerResult:
        """Run category checks sequentially (for debugging).

        Args:
            paper_data: Structured paper data

        Returns:
            LogicCheckerResult with aggregated issues
        """
        all_issues = []
        failed_categories = []
        successful_count = 0

        for category_name, checker in self.checkers.items():
            try:
                issues = self._run_category_check(category_name, checker, paper_data)
                successful_count += 1
                all_issues.extend(issues)
                logger.info(f"✓ {category_name}: Found {len(issues)} issues")
            except Exception as e:
                failed_categories.append(category_name)
                logger.warning(f"✗ {category_name}: Failed with error: {str(e)}")

        # Validate that at least some categories succeeded
        if successful_count == 0:
            raise ValueError(
                f"All {len(self.checkers)} category checks failed. "
                f"Failed categories: {', '.join(failed_categories)}"
            )

        logger.info(
            f"Logic check complete: {successful_count}/{len(self.checkers)} categories succeeded, "
            f"found {len(all_issues)} total issues"
        )

        return LogicCheckerResult(
            issues=all_issues,
            total_categories=len(self.checkers),
            successful_categories=successful_count,
            failed_categories=failed_categories,
        )

    def _run_category_check(
        self,
        category_name: str,
        checker,
        paper_data: PaperData,
    ) -> list[MethodologicalIssue]:
        """Run a single category check with error handling.

        Args:
            category_name: Name of the category being checked
            checker: Category checker instance
            paper_data: Structured paper data

        Returns:
            List of issues found by this category checker

        Raises:
            Exception: If the category check fails
        """
        try:
            logger.debug(f"Running {category_name} check...")
            issues = checker.check(paper_data)
            return issues
        except Exception as e:
            # Log the error and re-raise so executor can catch it
            logger.error(f"Category {category_name} failed: {str(e)}")
            raise

    def check_category(
        self,
        category_name: str,
        paper_data: PaperData,
    ) -> list[MethodologicalIssue]:
        """Check a single category (useful for testing individual checkers).

        Args:
            category_name: Name of the category to check
            paper_data: Structured paper data

        Returns:
            List of issues found by this category checker

        Raises:
            ValueError: If category_name is not valid
            Exception: If the category check fails
        """
        if category_name not in self.checkers:
            valid_categories = ', '.join(sorted(self.checkers.keys()))
            raise ValueError(
                f"Invalid category '{category_name}'. "
                f"Valid categories: {valid_categories}"
            )

        checker = self.checkers[category_name]
        return self._run_category_check(category_name, checker, paper_data)

    def get_categories(self) -> list[str]:
        """Get list of all available category names.

        Returns:
            List of category names that this checker supports
        """
        return sorted(self.checkers.keys())
