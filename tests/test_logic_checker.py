"""Unit tests for LogicChecker orchestrator."""

import pytest
from unittest.mock import Mock, patch, MagicMock

from src.logic_checker import LogicChecker, LogicCheckerResult
from src.claude_client import ClaudeClient
from src.models.issue import MethodologicalIssue, Severity, Evidence
from src.models.paper_data import PaperData, Metadata


@pytest.fixture
def mock_claude_client():
    """Create a mock Claude client."""
    client = Mock(spec=ClaudeClient)
    return client


@pytest.fixture
def sample_paper_data():
    """Create sample paper data for testing."""
    return PaperData(
        metadata=Metadata(
            title="Test Paper",
            authors=["Author One", "Author Two"],
            year=2024,
            venue="TestConf",
        ),
        abstract="This is a test paper abstract.",
        sections=[],
        tables=[],
        claims=[],
        experiments=[],
        references=[],
        full_text="Test paper full text.",
    )


@pytest.fixture
def sample_issue():
    """Create a sample methodological issue."""
    return MethodologicalIssue(
        category="data_leakage",
        severity=Severity.CRITICAL,
        confidence=0.9,
        title="Test data leakage",
        description="Test description",
        evidence=Evidence(
            section="Method",
            quote="Test quote",
        ),
        suggestions=["Fix this issue"],
    )


class TestLogicCheckerResult:
    """Test LogicCheckerResult class."""

    def test_init(self, sample_issue):
        """Test result initialization."""
        result = LogicCheckerResult(
            issues=[sample_issue],
            total_categories=9,
            successful_categories=8,
            failed_categories=["unfair_comparison"],
        )

        assert len(result.issues) == 1
        assert result.total_categories == 9
        assert result.successful_categories == 8
        assert result.failed_categories == ["unfair_comparison"]

    def test_is_partial(self, sample_issue):
        """Test is_partial property."""
        # Partial result (some failures)
        partial_result = LogicCheckerResult(
            issues=[sample_issue],
            total_categories=9,
            successful_categories=8,
            failed_categories=["unfair_comparison"],
        )
        assert partial_result.is_partial is True

        # Complete result (no failures)
        complete_result = LogicCheckerResult(
            issues=[sample_issue],
            total_categories=9,
            successful_categories=9,
            failed_categories=[],
        )
        assert complete_result.is_partial is False

    def test_success_rate(self, sample_issue):
        """Test success_rate property."""
        result = LogicCheckerResult(
            issues=[sample_issue],
            total_categories=9,
            successful_categories=6,
            failed_categories=["cat1", "cat2", "cat3"],
        )
        assert result.success_rate == pytest.approx(6 / 9)

        # Edge case: zero categories
        empty_result = LogicCheckerResult(
            issues=[],
            total_categories=0,
            successful_categories=0,
            failed_categories=[],
        )
        assert empty_result.success_rate == 0.0

    def test_to_dict(self, sample_issue):
        """Test to_dict serialization."""
        result = LogicCheckerResult(
            issues=[sample_issue],
            total_categories=9,
            successful_categories=8,
            failed_categories=["unfair_comparison"],
        )

        result_dict = result.to_dict()

        assert "issues" in result_dict
        assert "metadata" in result_dict
        assert len(result_dict["issues"]) == 1
        assert result_dict["metadata"]["total_categories"] == 9
        assert result_dict["metadata"]["successful_categories"] == 8
        assert result_dict["metadata"]["failed_categories"] == ["unfair_comparison"]
        assert result_dict["metadata"]["is_partial"] is True
        assert result_dict["metadata"]["success_rate"] == pytest.approx(8 / 9)


class TestLogicChecker:
    """Test LogicChecker class."""

    def test_init(self, mock_claude_client):
        """Test LogicChecker initialization."""
        checker = LogicChecker(mock_claude_client)

        assert checker.claude_client == mock_claude_client
        assert checker.enable_parallel is True
        assert len(checker.checkers) == 9

        # Verify all 9 categories are present
        expected_categories = {
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
        assert set(checker.checkers.keys()) == expected_categories

    def test_init_with_custom_settings(self, mock_claude_client):
        """Test initialization with custom settings."""
        checker = LogicChecker(
            mock_claude_client,
            max_workers=4,
            enable_parallel=False,
        )

        assert checker.max_workers == 4
        assert checker.enable_parallel is False

    def test_get_categories(self, mock_claude_client):
        """Test get_categories method."""
        checker = LogicChecker(mock_claude_client)
        categories = checker.get_categories()

        assert len(categories) == 9
        assert "data_leakage" in categories
        assert "unfair_comparison" in categories
        # Verify it's sorted
        assert categories == sorted(categories)

    def test_check_invalid_input(self, mock_claude_client):
        """Test check with invalid input."""
        checker = LogicChecker(mock_claude_client)

        with pytest.raises(ValueError, match="paper_data cannot be None"):
            checker.check(None)

    @patch("src.logic_checker.LogicChecker._check_parallel")
    def test_check_calls_parallel(self, mock_check_parallel, mock_claude_client, sample_paper_data):
        """Test that check calls parallel mode when enabled."""
        checker = LogicChecker(mock_claude_client, enable_parallel=True)
        mock_check_parallel.return_value = LogicCheckerResult(
            issues=[],
            total_categories=9,
            successful_categories=9,
            failed_categories=[],
        )

        result = checker.check(sample_paper_data)

        mock_check_parallel.assert_called_once_with(sample_paper_data)
        assert result is not None

    @patch("src.logic_checker.LogicChecker._check_sequential")
    def test_check_calls_sequential(self, mock_check_sequential, mock_claude_client, sample_paper_data):
        """Test that check calls sequential mode when parallel is disabled."""
        checker = LogicChecker(mock_claude_client, enable_parallel=False)
        mock_check_sequential.return_value = LogicCheckerResult(
            issues=[],
            total_categories=9,
            successful_categories=9,
            failed_categories=[],
        )

        result = checker.check(sample_paper_data)

        mock_check_sequential.assert_called_once_with(sample_paper_data)
        assert result is not None

    def test_check_sequential_all_success(self, mock_claude_client, sample_paper_data, sample_issue):
        """Test sequential check with all categories succeeding."""
        checker = LogicChecker(mock_claude_client, enable_parallel=False)

        # Mock all checkers to return empty lists
        for category_checker in checker.checkers.values():
            category_checker.check = Mock(return_value=[])

        # Make one checker return an issue
        checker.checkers["data_leakage"].check = Mock(return_value=[sample_issue])

        result = checker.check(sample_paper_data)

        assert len(result.issues) == 1
        assert result.successful_categories == 9
        assert len(result.failed_categories) == 0
        assert result.is_partial is False

    def test_check_sequential_partial_failure(self, mock_claude_client, sample_paper_data, sample_issue):
        """Test sequential check with some categories failing."""
        checker = LogicChecker(mock_claude_client, enable_parallel=False)

        # Mock most checkers to succeed
        for category_name, category_checker in checker.checkers.items():
            if category_name == "unfair_comparison":
                # This one fails
                category_checker.check = Mock(side_effect=Exception("API error"))
            elif category_name == "data_leakage":
                # This one returns an issue
                category_checker.check = Mock(return_value=[sample_issue])
            else:
                # Others succeed with no issues
                category_checker.check = Mock(return_value=[])

        result = checker.check(sample_paper_data)

        assert len(result.issues) == 1
        assert result.successful_categories == 8
        assert "unfair_comparison" in result.failed_categories
        assert result.is_partial is True

    def test_check_sequential_all_fail(self, mock_claude_client, sample_paper_data):
        """Test sequential check with all categories failing."""
        checker = LogicChecker(mock_claude_client, enable_parallel=False)

        # Mock all checkers to fail
        for category_checker in checker.checkers.values():
            category_checker.check = Mock(side_effect=Exception("API error"))

        with pytest.raises(ValueError, match="All 9 category checks failed"):
            checker.check(sample_paper_data)

    def test_check_category_success(self, mock_claude_client, sample_paper_data, sample_issue):
        """Test checking a single category."""
        checker = LogicChecker(mock_claude_client)

        # Mock the data_leakage checker
        checker.checkers["data_leakage"].check = Mock(return_value=[sample_issue])

        issues = checker.check_category("data_leakage", sample_paper_data)

        assert len(issues) == 1
        assert issues[0] == sample_issue

    def test_check_category_invalid(self, mock_claude_client, sample_paper_data):
        """Test checking an invalid category."""
        checker = LogicChecker(mock_claude_client)

        with pytest.raises(ValueError, match="Invalid category 'invalid_category'"):
            checker.check_category("invalid_category", sample_paper_data)

    def test_run_category_check_success(self, mock_claude_client, sample_paper_data, sample_issue):
        """Test _run_category_check with success."""
        checker = LogicChecker(mock_claude_client)

        mock_checker = Mock()
        mock_checker.check = Mock(return_value=[sample_issue])

        issues = checker._run_category_check("test_category", mock_checker, sample_paper_data)

        assert len(issues) == 1
        assert issues[0] == sample_issue

    def test_run_category_check_failure(self, mock_claude_client, sample_paper_data):
        """Test _run_category_check with failure."""
        checker = LogicChecker(mock_claude_client)

        mock_checker = Mock()
        mock_checker.check = Mock(side_effect=Exception("API error"))

        with pytest.raises(Exception, match="API error"):
            checker._run_category_check("test_category", mock_checker, sample_paper_data)


class TestLogicCheckerIntegration:
    """Integration tests for LogicChecker with mocked checkers."""

    def test_full_check_mixed_results(self, mock_claude_client, sample_paper_data):
        """Test full check with mixed results across categories."""
        checker = LogicChecker(mock_claude_client, enable_parallel=False)

        # Create different issues for different categories
        data_leakage_issue = MethodologicalIssue(
            category="data_leakage",
            severity=Severity.CRITICAL,
            confidence=0.9,
            title="Train/test contamination",
            description="Test data overlaps with training data",
            evidence=Evidence(section="Method"),
            suggestions=["Ensure proper data split"],
        )

        unfair_comparison_issue = MethodologicalIssue(
            category="unfair_comparison",
            severity=Severity.CRITICAL,
            confidence=0.85,
            title="Outdated baselines",
            description="Comparing against old methods",
            evidence=Evidence(section="Results"),
            suggestions=["Use recent baselines"],
        )

        # Mock checkers
        checker.checkers["data_leakage"].check = Mock(return_value=[data_leakage_issue])
        checker.checkers["unfair_comparison"].check = Mock(return_value=[unfair_comparison_issue])
        checker.checkers["cherry_picking"].check = Mock(side_effect=Exception("API timeout"))

        # Other checkers return empty results
        for category_name in ["claim_evidence_gap", "missing_ablation", "statistical_validity",
                              "implicit_assumption", "reproducibility", "causal_overclaim"]:
            checker.checkers[category_name].check = Mock(return_value=[])

        result = checker.check(sample_paper_data)

        assert len(result.issues) == 2
        assert result.successful_categories == 8
        assert result.failed_categories == ["cherry_picking"]
        assert result.success_rate == pytest.approx(8 / 9)

        # Verify both issues are present
        categories = [issue.category for issue in result.issues]
        assert "data_leakage" in categories
        assert "unfair_comparison" in categories
