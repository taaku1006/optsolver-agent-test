"""Unit tests for category checkers."""

import json
import pytest
from unittest.mock import Mock, MagicMock

from src.categories.base import BaseChecker
from src.categories.data_leakage import DataLeakageChecker
from src.categories.unfair_comparison import UnfairComparisonChecker
from src.categories.claim_evidence_gap import ClaimEvidenceGapChecker
from src.categories.cherry_picking import CherryPickingChecker
from src.categories.missing_ablation import MissingAblationChecker
from src.categories.statistical_validity import StatisticalValidityChecker
from src.categories.implicit_assumption import ImplicitAssumptionChecker
from src.categories.reproducibility import ReproducibilityChecker
from src.categories.causal_overclaim import CausalOverclaimChecker
from src.claude_client import ClaudeClient, ClaudeClientError, ClaudeResponse
from src.models.issue import MethodologicalIssue, Severity, Evidence
from src.models.paper_data import PaperData, Metadata, Section


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
            title="Test Paper on Machine Learning",
            authors=["Author One", "Author Two"],
            year=2024,
            venue="TestConf",
        ),
        abstract="This paper presents a novel approach to machine learning.",
        sections=[
            Section(
                title="Introduction",
                content="We introduce a new method for classification."
            ),
            Section(
                title="Method",
                content="Our method uses a neural network with 10 layers."
            ),
            Section(
                title="Experiments",
                content="We evaluate on MNIST dataset and achieve 99% accuracy."
            ),
        ],
        tables=[],
        claims=["Our method achieves state-of-the-art performance"],
        experiments=[],
        references=[],
        full_text="Test paper full text.",
    )


@pytest.fixture
def sample_claude_response():
    """Create a sample Claude response with valid JSON."""
    return ClaudeResponse(
        content=json.dumps([
            {
                "severity": "critical",
                "confidence": 0.9,
                "title": "Test issue",
                "description": "This is a test issue description",
                "evidence_section": "Method",
                "evidence_quote": "Test quote from the paper",
                "suggestions": ["Fix this issue", "Add more details"]
            }
        ]),
        usage_input_tokens=100,
        usage_output_tokens=50,
    )


@pytest.fixture
def sample_claude_response_markdown():
    """Create a sample Claude response with JSON in markdown code block."""
    json_content = [
        {
            "severity": "warning",
            "confidence": 0.75,
            "title": "Test warning",
            "description": "This is a warning",
            "evidence_section": "Results",
            "suggestions": ["Consider this"]
        }
    ]
    return ClaudeResponse(
        content=f"```json\n{json.dumps(json_content, indent=2)}\n```",
        usage_input_tokens=100,
        usage_output_tokens=50,
    )


@pytest.fixture
def sample_claude_response_empty():
    """Create a sample Claude response with empty issues list."""
    return ClaudeResponse(
        content="[]",
        usage_input_tokens=100,
        usage_output_tokens=20,
    )


class TestBaseChecker:
    """Test BaseChecker base class."""

    def test_init(self, mock_claude_client):
        """Test BaseChecker initialization."""
        # Cannot instantiate abstract class directly, so we test via subclass
        checker = DataLeakageChecker(mock_claude_client)

        assert checker.claude_client == mock_claude_client
        assert checker.category == "data_leakage"

    def test_format_paper_data(self, mock_claude_client, sample_paper_data):
        """Test _format_paper_data method."""
        checker = DataLeakageChecker(mock_claude_client)

        formatted = checker._format_paper_data(sample_paper_data)

        # Verify formatted output contains key information
        assert "Test Paper on Machine Learning" in formatted
        assert "Author One" in formatted
        assert "2024" in formatted
        assert "This paper presents a novel approach" in formatted
        assert "Introduction" in formatted
        assert "Method" in formatted
        assert "Our method achieves state-of-the-art performance" in formatted

    def test_format_paper_data_with_tables(self, mock_claude_client):
        """Test _format_paper_data with tables."""
        from src.models.paper_data import Table

        checker = DataLeakageChecker(mock_claude_client)
        paper_data = PaperData(
            metadata=Metadata(title="Test", authors=[], year=2024),
            abstract="Test abstract",
            sections=[],
            tables=[
                Table(id="Table 1", caption="Test table", content="Row 1 | Row 2")
            ],
            claims=[],
            experiments=[],
            references=[],
            full_text="Test",
        )

        formatted = checker._format_paper_data(paper_data)

        assert "Table 1" in formatted
        assert "Test table" in formatted
        assert "Row 1 | Row 2" in formatted

    def test_repr(self, mock_claude_client):
        """Test __repr__ method."""
        checker = DataLeakageChecker(mock_claude_client)

        repr_str = repr(checker)

        assert "DataLeakageChecker" in repr_str
        assert "data_leakage" in repr_str


class TestDataLeakageChecker:
    """Test DataLeakageChecker."""

    def test_init(self, mock_claude_client):
        """Test initialization."""
        checker = DataLeakageChecker(mock_claude_client)

        assert checker.category == "data_leakage"
        assert checker.claude_client == mock_claude_client

    def test_check_success(self, mock_claude_client, sample_paper_data, sample_claude_response):
        """Test successful check with issues found."""
        mock_claude_client.generate.return_value = sample_claude_response

        checker = DataLeakageChecker(mock_claude_client)
        issues = checker.check(sample_paper_data)

        assert len(issues) == 1
        assert issues[0].category == "data_leakage"
        assert issues[0].severity == Severity.CRITICAL
        assert issues[0].confidence == 0.9
        assert issues[0].title == "Test issue"
        assert issues[0].evidence.section == "Method"
        assert len(issues[0].suggestions) == 2

    def test_check_no_issues(self, mock_claude_client, sample_paper_data, sample_claude_response_empty):
        """Test check with no issues found."""
        mock_claude_client.generate.return_value = sample_claude_response_empty

        checker = DataLeakageChecker(mock_claude_client)
        issues = checker.check(sample_paper_data)

        assert len(issues) == 0

    def test_check_none_paper_data(self, mock_claude_client):
        """Test check with None paper data."""
        checker = DataLeakageChecker(mock_claude_client)

        with pytest.raises(ValueError, match="paper_data cannot be None"):
            checker.check(None)

    def test_check_claude_error(self, mock_claude_client, sample_paper_data):
        """Test check when Claude API fails."""
        mock_claude_client.generate.side_effect = ClaudeClientError("API error")

        checker = DataLeakageChecker(mock_claude_client)

        with pytest.raises(ClaudeClientError, match="Failed to check data leakage"):
            checker.check(sample_paper_data)

    def test_parse_response_valid_json(self, mock_claude_client):
        """Test parsing valid JSON response."""
        checker = DataLeakageChecker(mock_claude_client)

        json_content = json.dumps([{"test": "data"}])
        result = checker._parse_response(json_content)

        assert len(result) == 1
        assert result[0]["test"] == "data"

    def test_parse_response_markdown(self, mock_claude_client):
        """Test parsing JSON wrapped in markdown code block."""
        checker = DataLeakageChecker(mock_claude_client)

        content = "```json\n[{\"test\": \"data\"}]\n```"
        result = checker._parse_response(content)

        assert len(result) == 1
        assert result[0]["test"] == "data"

    def test_parse_response_invalid_json(self, mock_claude_client):
        """Test parsing invalid JSON."""
        checker = DataLeakageChecker(mock_claude_client)

        with pytest.raises(ValueError, match="Invalid JSON response"):
            checker._parse_response("not valid json")

    def test_parse_response_not_array(self, mock_claude_client):
        """Test parsing JSON that is not an array."""
        checker = DataLeakageChecker(mock_claude_client)

        with pytest.raises(ValueError, match="Expected JSON array"):
            checker._parse_response('{"test": "data"}')

    def test_dict_to_issue_complete(self, mock_claude_client):
        """Test converting complete issue dict to MethodologicalIssue."""
        checker = DataLeakageChecker(mock_claude_client)

        issue_dict = {
            "severity": "critical",
            "confidence": 0.85,
            "title": "Data leakage detected",
            "description": "Test set overlaps with training set",
            "evidence_section": "Method",
            "evidence_quote": "We split the data randomly",
            "evidence_table": "Table 1",
            "suggestions": ["Use proper train/test split"]
        }

        issue = checker._dict_to_issue(issue_dict)

        assert issue is not None
        assert issue.category == "data_leakage"
        assert issue.severity == Severity.CRITICAL
        assert issue.confidence == 0.85
        assert issue.title == "Data leakage detected"
        assert issue.description == "Test set overlaps with training set"
        assert issue.evidence.section == "Method"
        assert issue.evidence.quote == "We split the data randomly"
        assert issue.evidence.table_reference == "Table 1"
        assert len(issue.suggestions) == 1

    def test_dict_to_issue_minimal(self, mock_claude_client):
        """Test converting minimal issue dict with defaults."""
        checker = DataLeakageChecker(mock_claude_client)

        issue_dict = {}

        issue = checker._dict_to_issue(issue_dict)

        assert issue is not None
        assert issue.category == "data_leakage"
        assert issue.severity == Severity.WARNING  # default
        assert issue.confidence == 0.7  # default
        assert issue.title == "Data leakage detected"  # default
        assert len(issue.suggestions) == 0

    def test_dict_to_issue_invalid(self, mock_claude_client, capsys):
        """Test converting invalid issue dict."""
        checker = DataLeakageChecker(mock_claude_client)

        issue_dict = {"confidence": "invalid"}  # confidence should be float

        issue = checker._dict_to_issue(issue_dict)

        # Should return None and print warning
        assert issue is None
        captured = capsys.readouterr()
        assert "Warning: Failed to parse issue" in captured.out


class TestUnfairComparisonChecker:
    """Test UnfairComparisonChecker."""

    def test_init(self, mock_claude_client):
        """Test initialization."""
        checker = UnfairComparisonChecker(mock_claude_client)

        assert checker.category == "unfair_comparison"
        assert checker.claude_client == mock_claude_client

    def test_check_success(self, mock_claude_client, sample_paper_data, sample_claude_response):
        """Test successful check."""
        mock_claude_client.generate.return_value = sample_claude_response

        checker = UnfairComparisonChecker(mock_claude_client)
        issues = checker.check(sample_paper_data)

        assert len(issues) == 1
        assert issues[0].category == "unfair_comparison"

    def test_check_api_error(self, mock_claude_client, sample_paper_data):
        """Test check when API fails."""
        mock_claude_client.generate.side_effect = ClaudeClientError("API timeout")

        checker = UnfairComparisonChecker(mock_claude_client)

        with pytest.raises(ClaudeClientError, match="Failed to check unfair comparison"):
            checker.check(sample_paper_data)


class TestClaimEvidenceGapChecker:
    """Test ClaimEvidenceGapChecker."""

    def test_init(self, mock_claude_client):
        """Test initialization."""
        checker = ClaimEvidenceGapChecker(mock_claude_client)

        assert checker.category == "claim_evidence_gap"
        assert checker.claude_client == mock_claude_client

    def test_check_success(self, mock_claude_client, sample_paper_data, sample_claude_response):
        """Test successful check."""
        mock_claude_client.generate.return_value = sample_claude_response

        checker = ClaimEvidenceGapChecker(mock_claude_client)
        issues = checker.check(sample_paper_data)

        assert len(issues) == 1
        assert issues[0].category == "claim_evidence_gap"

    def test_check_with_markdown_response(self, mock_claude_client, sample_paper_data, sample_claude_response_markdown):
        """Test check with markdown-wrapped response."""
        mock_claude_client.generate.return_value = sample_claude_response_markdown

        checker = ClaimEvidenceGapChecker(mock_claude_client)
        issues = checker.check(sample_paper_data)

        assert len(issues) == 1
        assert issues[0].severity == Severity.WARNING


class TestCherryPickingChecker:
    """Test CherryPickingChecker."""

    def test_init(self, mock_claude_client):
        """Test initialization."""
        checker = CherryPickingChecker(mock_claude_client)

        assert checker.category == "cherry_picking"
        assert checker.claude_client == mock_claude_client

    def test_check_success(self, mock_claude_client, sample_paper_data, sample_claude_response):
        """Test successful check."""
        mock_claude_client.generate.return_value = sample_claude_response

        checker = CherryPickingChecker(mock_claude_client)
        issues = checker.check(sample_paper_data)

        assert len(issues) == 1
        assert issues[0].category == "cherry_picking"


class TestMissingAblationChecker:
    """Test MissingAblationChecker."""

    def test_init(self, mock_claude_client):
        """Test initialization."""
        checker = MissingAblationChecker(mock_claude_client)

        assert checker.category == "missing_ablation"
        assert checker.claude_client == mock_claude_client

    def test_check_success(self, mock_claude_client, sample_paper_data, sample_claude_response):
        """Test successful check."""
        mock_claude_client.generate.return_value = sample_claude_response

        checker = MissingAblationChecker(mock_claude_client)
        issues = checker.check(sample_paper_data)

        assert len(issues) == 1
        assert issues[0].category == "missing_ablation"


class TestStatisticalValidityChecker:
    """Test StatisticalValidityChecker."""

    def test_init(self, mock_claude_client):
        """Test initialization."""
        checker = StatisticalValidityChecker(mock_claude_client)

        assert checker.category == "statistical_validity"
        assert checker.claude_client == mock_claude_client

    def test_check_success(self, mock_claude_client, sample_paper_data, sample_claude_response):
        """Test successful check."""
        mock_claude_client.generate.return_value = sample_claude_response

        checker = StatisticalValidityChecker(mock_claude_client)
        issues = checker.check(sample_paper_data)

        assert len(issues) == 1
        assert issues[0].category == "statistical_validity"


class TestImplicitAssumptionChecker:
    """Test ImplicitAssumptionChecker."""

    def test_init(self, mock_claude_client):
        """Test initialization."""
        checker = ImplicitAssumptionChecker(mock_claude_client)

        assert checker.category == "implicit_assumption"
        assert checker.claude_client == mock_claude_client

    def test_check_success(self, mock_claude_client, sample_paper_data, sample_claude_response):
        """Test successful check."""
        mock_claude_client.generate.return_value = sample_claude_response

        checker = ImplicitAssumptionChecker(mock_claude_client)
        issues = checker.check(sample_paper_data)

        assert len(issues) == 1
        assert issues[0].category == "implicit_assumption"


class TestReproducibilityChecker:
    """Test ReproducibilityChecker."""

    def test_init(self, mock_claude_client):
        """Test initialization."""
        checker = ReproducibilityChecker(mock_claude_client)

        assert checker.category == "reproducibility"
        assert checker.claude_client == mock_claude_client

    def test_check_success(self, mock_claude_client, sample_paper_data, sample_claude_response):
        """Test successful check."""
        mock_claude_client.generate.return_value = sample_claude_response

        checker = ReproducibilityChecker(mock_claude_client)
        issues = checker.check(sample_paper_data)

        assert len(issues) == 1
        assert issues[0].category == "reproducibility"


class TestCausalOverclaimChecker:
    """Test CausalOverclaimChecker."""

    def test_init(self, mock_claude_client):
        """Test initialization."""
        checker = CausalOverclaimChecker(mock_claude_client)

        assert checker.category == "causal_overclaim"
        assert checker.claude_client == mock_claude_client

    def test_check_success(self, mock_claude_client, sample_paper_data, sample_claude_response):
        """Test successful check."""
        mock_claude_client.generate.return_value = sample_claude_response

        checker = CausalOverclaimChecker(mock_claude_client)
        issues = checker.check(sample_paper_data)

        assert len(issues) == 1
        assert issues[0].category == "causal_overclaim"


class TestCategoryCheckersIntegration:
    """Integration tests for all category checkers."""

    def test_all_checkers_have_correct_category(self, mock_claude_client):
        """Test that all checkers have correct category names."""
        checkers = [
            (DataLeakageChecker, "data_leakage"),
            (UnfairComparisonChecker, "unfair_comparison"),
            (ClaimEvidenceGapChecker, "claim_evidence_gap"),
            (CherryPickingChecker, "cherry_picking"),
            (MissingAblationChecker, "missing_ablation"),
            (StatisticalValidityChecker, "statistical_validity"),
            (ImplicitAssumptionChecker, "implicit_assumption"),
            (ReproducibilityChecker, "reproducibility"),
            (CausalOverclaimChecker, "causal_overclaim"),
        ]

        for checker_class, expected_category in checkers:
            checker = checker_class(mock_claude_client)
            assert checker.category == expected_category

    def test_all_checkers_handle_empty_results(self, mock_claude_client, sample_paper_data, sample_claude_response_empty):
        """Test that all checkers handle empty results correctly."""
        mock_claude_client.generate.return_value = sample_claude_response_empty

        checkers = [
            DataLeakageChecker(mock_claude_client),
            UnfairComparisonChecker(mock_claude_client),
            ClaimEvidenceGapChecker(mock_claude_client),
            CherryPickingChecker(mock_claude_client),
            MissingAblationChecker(mock_claude_client),
            StatisticalValidityChecker(mock_claude_client),
            ImplicitAssumptionChecker(mock_claude_client),
            ReproducibilityChecker(mock_claude_client),
            CausalOverclaimChecker(mock_claude_client),
        ]

        for checker in checkers:
            issues = checker.check(sample_paper_data)
            assert len(issues) == 0

    def test_all_checkers_handle_api_error(self, mock_claude_client, sample_paper_data):
        """Test that all checkers handle API errors correctly."""
        mock_claude_client.generate.side_effect = ClaudeClientError("API error")

        checkers = [
            DataLeakageChecker(mock_claude_client),
            UnfairComparisonChecker(mock_claude_client),
            ClaimEvidenceGapChecker(mock_claude_client),
            CherryPickingChecker(mock_claude_client),
            MissingAblationChecker(mock_claude_client),
            StatisticalValidityChecker(mock_claude_client),
            ImplicitAssumptionChecker(mock_claude_client),
            ReproducibilityChecker(mock_claude_client),
            CausalOverclaimChecker(mock_claude_client),
        ]

        for checker in checkers:
            with pytest.raises(ClaudeClientError):
                checker.check(sample_paper_data)

    def test_all_checkers_reject_none_input(self, mock_claude_client):
        """Test that all checkers reject None input."""
        checkers = [
            DataLeakageChecker(mock_claude_client),
            UnfairComparisonChecker(mock_claude_client),
            ClaimEvidenceGapChecker(mock_claude_client),
            CherryPickingChecker(mock_claude_client),
            MissingAblationChecker(mock_claude_client),
            StatisticalValidityChecker(mock_claude_client),
            ImplicitAssumptionChecker(mock_claude_client),
            ReproducibilityChecker(mock_claude_client),
            CausalOverclaimChecker(mock_claude_client),
        ]

        for checker in checkers:
            with pytest.raises(ValueError, match="paper_data cannot be None"):
                checker.check(None)

    def test_multiple_issues_in_response(self, mock_claude_client, sample_paper_data):
        """Test parsing response with multiple issues."""
        response = ClaudeResponse(
            content=json.dumps([
                {
                    "severity": "critical",
                    "confidence": 0.9,
                    "title": "First issue",
                    "description": "Description 1",
                    "evidence_section": "Method",
                    "suggestions": ["Fix 1"]
                },
                {
                    "severity": "warning",
                    "confidence": 0.7,
                    "title": "Second issue",
                    "description": "Description 2",
                    "evidence_section": "Results",
                    "suggestions": ["Fix 2"]
                },
            ]),
            usage_input_tokens=100,
            usage_output_tokens=100,
        )
        mock_claude_client.generate.return_value = response

        checker = DataLeakageChecker(mock_claude_client)
        issues = checker.check(sample_paper_data)

        assert len(issues) == 2
        assert issues[0].title == "First issue"
        assert issues[1].title == "Second issue"
        assert issues[0].severity == Severity.CRITICAL
        assert issues[1].severity == Severity.WARNING

    def test_parse_response_handles_extra_whitespace(self, mock_claude_client):
        """Test that _parse_response handles extra whitespace."""
        checker = DataLeakageChecker(mock_claude_client)

        content = "   \n\n  [{}]  \n\n  "
        result = checker._parse_response(content)

        assert len(result) == 1

    def test_severity_mapping(self, mock_claude_client):
        """Test that all severity levels are correctly mapped."""
        checker = DataLeakageChecker(mock_claude_client)

        for severity_str in ["critical", "warning", "info"]:
            issue_dict = {
                "severity": severity_str,
                "confidence": 0.8,
                "title": "Test",
                "description": "Test description",
            }

            issue = checker._dict_to_issue(issue_dict)

            assert issue is not None
            assert issue.severity.value == severity_str
