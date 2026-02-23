# Logic & Methodology Verification (Stage 2 Pipeline)

**Automated detection of methodological flaws in research papers using structured, systematic analysis.**

This is Stage 2 of the Paper Verifier pipeline — the core differentiator that detects subtle methodological issues that even experienced reviewers miss under time pressure. It analyzes structured paper data to identify 9 categories of methodological flaws with severity levels and confidence scores.

## Features

The Logic Checker systematically examines papers for 9 categories of methodological issues:

| Category | Description | Example Issue |
|----------|-------------|---------------|
| **claim_evidence_gap** | Claims lacking supporting evidence or misrepresenting results | "Best performance" claim without statistical comparison |
| **data_leakage** | Train/test contamination, temporal leakage, future information | Testing on data that overlaps with training set |
| **unfair_comparison** | Misleading baseline comparisons, cherry-picked metrics | Comparing against outdated 2015 baselines in 2024 |
| **cherry_picking** | Selective reporting, missing standard benchmarks | Reporting only favorable metrics, omitting standard tests |
| **missing_ablation** | Insufficient validation of design choices | No ablation study to validate component contributions |
| **statistical_validity** | Missing significance tests, error bars, statistical rigor | No confidence intervals or significance tests reported |
| **implicit_assumption** | Unstated assumptions about data, deployment, problem structure | Assuming i.i.d. data without verification |
| **reproducibility** | Missing implementation details needed to replicate work | No hyperparameters, seeds, or code availability |
| **causal_overclaim** | Causal claims not supported by experimental design | Claiming causation from observational data |

Each detected issue includes:
- **Severity level**: `critical`, `warning`, or `info`
- **Confidence score**: 0.0 to 1.0 indicating detector confidence
- **Evidence**: Specific references (section, quote, table, page number)
- **Suggestions**: Actionable recommendations to address the issue

## Installation

### Prerequisites
- Python 3.10 or higher
- Anthropic API key for Claude access

### Setup

1. Clone the repository and navigate to the project directory:
```bash
cd /path/to/logic-methodology-verification
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Set your Anthropic API key:
```bash
export ANTHROPIC_API_KEY="sk-ant-..."
```

Or create a `.env` file:
```bash
ANTHROPIC_API_KEY=sk-ant-...
```

## Usage

### Command-Line Interface

The primary interface is a CLI that processes paper data (JSON from Stage 1) and outputs detected issues:

**Basic usage:**
```bash
python -m src.main paper_data.json
```

**Save results to file:**
```bash
python -m src.main paper_data.json --output results.json
```

**Full options:**
```bash
python -m src.main paper_data.json \
  --output results.json \
  --api-key sk-ant-... \
  --model claude-3-sonnet-20240229 \
  --max-workers 4 \
  --verbose
```

**CLI Options:**

| Option | Description | Default |
|--------|-------------|---------|
| `input_file` | Path to paper data JSON (from Stage 1) | Required |
| `--output` | Path to save results JSON | `stdout` |
| `--api-key` | Anthropic API key | `$ANTHROPIC_API_KEY` |
| `--model` | Claude model to use | `claude-3-sonnet-20240229` |
| `--max-workers` | Parallel worker threads | `4` |
| `--no-parallel` | Disable parallel execution | `False` |
| `--timeout` | Request timeout in seconds | `60` |
| `--max-retries` | Max retry attempts for API calls | `3` |
| `--verbose` | Enable verbose logging | `False` |
| `--version` | Show version and exit | - |

### Programmatic API

Import and use the `LogicChecker` class directly:

```python
from src.logic_checker import LogicChecker
from src.claude_client import ClaudeClient
from src.models.paper_data import PaperData
import json

# Load paper data
with open("paper_data.json") as f:
    paper_dict = json.load(f)
    paper_data = PaperData(**paper_dict)

# Initialize Claude client and Logic Checker
claude_client = ClaudeClient(api_key="sk-ant-...")
checker = LogicChecker(claude_client)

# Run all checks in parallel
result = checker.check_all(paper_data)

# Access results
print(f"Found {len(result.issues)} issues")
print(f"Success rate: {result.success_rate:.1%}")

for issue in result.issues:
    print(f"\n[{issue.severity.value.upper()}] {issue.category}")
    print(f"  {issue.title}")
    print(f"  Confidence: {issue.confidence:.2f}")
    print(f"  Evidence: {issue.evidence.section}")
```

**Run individual category checks:**
```python
# Check only for data leakage
data_leakage_issues = checker.check_category(paper_data, "data_leakage")

# Check only for unfair comparisons
unfair_comparison_issues = checker.check_category(paper_data, "unfair_comparison")
```

**Sequential execution (no parallelism):**
```python
result = checker.check_all(paper_data, parallel=False)
```

## API Description

### Input Format (from Stage 1)

The Logic Checker expects JSON input conforming to the `PaperData` model:

```json
{
  "metadata": {
    "title": "Paper Title",
    "authors": ["Author 1", "Author 2"],
    "year": 2024,
    "venue": "NeurIPS",
    "arxiv_id": "2401.12345"
  },
  "abstract": "Paper abstract text...",
  "sections": [
    {
      "title": "Introduction",
      "content": "Section text content...",
      "page": 1,
      "subsections": []
    }
  ],
  "tables": [
    {
      "id": "Table 1",
      "caption": "Experimental results",
      "content": "Method | Accuracy\nOurs | 95%",
      "page": 5
    }
  ],
  "claims": [
    {
      "text": "Our method outperforms all baselines",
      "section": "Results",
      "claim_type": "main_contribution",
      "supporting_evidence": ["Table 1"]
    }
  ],
  "experiments": [
    {
      "name": "Benchmark evaluation",
      "dataset": "ImageNet",
      "metrics": ["accuracy", "F1"],
      "baselines": ["ResNet", "VGG"],
      "results": {"accuracy": 0.95}
    }
  ],
  "references": ["Smith et al. 2023", "..."],
  "full_text": "Complete paper text..."
}
```

### Output Format (to Stage 3)

The Logic Checker outputs JSON with detected issues and metadata:

```json
{
  "issues": [
    {
      "category": "unfair_comparison",
      "severity": "critical",
      "confidence": 0.85,
      "title": "Comparison against outdated baselines",
      "description": "The paper compares against baselines from 2015...",
      "evidence": {
        "section": "Experimental Results",
        "quote": "We compare against OR-Tools (2015 version)...",
        "table_reference": "Table 1",
        "page": 5
      },
      "suggestions": [
        "Include comparison with state-of-the-art methods from 2023-2024",
        "Justify the choice of baselines if older methods are used"
      ]
    }
  ],
  "metadata": {
    "total_issues": 3,
    "issues_by_severity": {
      "critical": 1,
      "warning": 2,
      "info": 0
    },
    "issues_by_category": {
      "unfair_comparison": 1,
      "data_leakage": 1,
      "missing_ablation": 1
    },
    "categories_checked": 9,
    "categories_succeeded": 9,
    "categories_failed": [],
    "success_rate": 1.0,
    "is_partial": false
  }
}
```

### Data Models

**MethodologicalIssue:**
- `category`: One of 9 issue categories (validated)
- `severity`: Enum (`critical`, `warning`, `info`)
- `confidence`: Float (0.0 to 1.0)
- `title`: Short issue description
- `description`: Detailed explanation
- `evidence`: Evidence object with section/quote/table/page references
- `suggestions`: List of actionable recommendations

**PaperData:**
- `metadata`: Title, authors, year, venue, DOI, arXiv ID
- `abstract`: Paper abstract text
- `sections`: List of sections with title, content, page, subsections
- `tables`: List of tables/figures with ID, caption, content, data
- `claims`: List of claims with text, section, type, evidence
- `experiments`: List of experiments with datasets, metrics, baselines
- `references`: Citation strings
- `full_text`: Complete paper text (optional)

## Test Case Examples

The project includes two validated test cases demonstrating known methodological issues:

### Example 1: AlphaOPT Paper (Unfair Comparison)

**Input:** `tests/fixtures/alphaotp_paper.json`

**Known Issue:** Compares against outdated baselines (OR-Tools 2015, methods from 2015-2019) in a 2024 paper

**Expected Detection:**
```bash
python -m src.main tests/fixtures/alphaotp_paper.json
```

**Output snippet:**
```json
{
  "category": "unfair_comparison",
  "severity": "critical",
  "confidence": 0.90,
  "title": "Comparison against outdated baselines from 2015",
  "evidence": {
    "section": "Experimental Results",
    "quote": "For TSP, we compare against...OR-Tools library (2015 version)",
    "table_reference": "Table 1"
  },
  "suggestions": [
    "Include comparisons with recent state-of-the-art methods (2023-2024)",
    "Use current versions of baseline libraries"
  ]
}
```

### Example 2: OR-R1 Paper (Data Leakage)

**Input:** `tests/fixtures/or_r1_paper.json`

**Known Issue:** Tests on same VMs used in training, temporal leakage in time-series data

**Expected Detection:**
```bash
python -m src.main tests/fixtures/or_r1_paper.json
```

**Output snippet:**
```json
{
  "category": "data_leakage",
  "severity": "critical",
  "confidence": 0.88,
  "title": "Temporal leakage in time-series train/test split",
  "evidence": {
    "section": "Experimental Setup",
    "quote": "training period: 2023-01...test period: 2023-08-15 to 2023-09-15",
    "page": 4
  },
  "suggestions": [
    "Use strict temporal split with gap period between train and test",
    "Ensure test data comes strictly after training data"
  ]
}
```

### Running Test Cases

Run the test suite to verify both examples:

```bash
# All tests
pytest tests/ -v

# Integration tests only (includes known test cases)
pytest tests/test_integration.py -v

# Specific test case
pytest tests/test_integration.py::TestAlphaOPTIntegration -v
pytest tests/test_integration.py::TestORR1Integration -v
```

## Development

### Running Tests

```bash
# Run all tests with coverage
pytest tests/ -v --cov=src --cov-report=term-missing

# Run specific test file
pytest tests/test_logic_checker.py -v

# Run integration tests
pytest tests/test_integration.py -v

# Run category checker tests
pytest tests/test_categories.py -v
```

**Coverage target:** >80% code coverage

### Type Checking

```bash
mypy src/
```

### Linting

```bash
# Check for issues
ruff check src/

# Auto-fix issues
ruff check --fix src/
```

### Project Structure

```
.
├── src/
│   ├── __init__.py
│   ├── main.py                    # CLI entry point
│   ├── logic_checker.py           # Main orchestrator
│   ├── claude_client.py           # Claude API client wrapper
│   ├── prompts.py                 # Category-specific prompts
│   ├── models/
│   │   ├── __init__.py
│   │   ├── issue.py               # MethodologicalIssue, Severity, Evidence
│   │   └── paper_data.py          # PaperData and related models
│   └── categories/
│       ├── __init__.py
│       ├── base.py                # BaseChecker abstract class
│       ├── claim_evidence_gap.py
│       ├── data_leakage.py
│       ├── unfair_comparison.py
│       ├── cherry_picking.py
│       ├── missing_ablation.py
│       ├── statistical_validity.py
│       ├── implicit_assumption.py
│       ├── reproducibility.py
│       └── causal_overclaim.py
├── tests/
│   ├── __init__.py
│   ├── test_logic_checker.py      # Unit tests for orchestrator
│   ├── test_integration.py        # Integration tests (AlphaOPT, OR-R1)
│   ├── test_categories.py         # Unit tests for category checkers
│   └── fixtures/
│       ├── alphaotp_paper.json    # Test case: unfair comparison
│       └── or_r1_paper.json       # Test case: data leakage
├── requirements.txt
├── pyproject.toml
└── README.md
```

## Pipeline Context

This is **Stage 2** of the Paper Verifier pipeline:

```
┌──────────────┐    ┌──────────────┐    ┌──────────────┐
│   Stage 1    │───▶│   Stage 2    │───▶│   Stage 3    │
│ PDF Extract  │    │ Logic Check  │    │  Report Gen  │
└──────────────┘    └──────────────┘    └──────────────┘
     Upload             (This repo)        Presentation
     Parse              9 Categories       Synthesis
     Structure          Detect Flaws       Visualize
```

### Input from Stage 1
- Structured paper data (JSON)
- Sections, tables, claims, experiments extracted from PDF
- Metadata and citations parsed

### Output to Stage 3
- List of detected methodological issues
- Severity levels and confidence scores
- Evidence references for each issue
- Actionable suggestions for improvement

### Design Principles

1. **Parallel Execution**: All 9 category checks run independently and in parallel for speed
2. **Graceful Degradation**: Returns partial results if some category checks fail
3. **Structured Output**: Pydantic models ensure type safety and schema validation
4. **Evidence-Based**: Every issue includes specific evidence (section, quote, table)
5. **Actionable**: Each issue includes suggestions for how to address it

## Architecture

### Core Components

1. **LogicChecker** (`src/logic_checker.py`)
   - Orchestrates all 9 category checkers
   - Manages parallel execution with ThreadPoolExecutor
   - Implements graceful fallback for partial failures
   - Aggregates results and metadata

2. **ClaudeClient** (`src/claude_client.py`)
   - Wraps Anthropic SDK with error handling
   - Implements retry logic with exponential backoff
   - Handles rate limits and transient errors
   - Provides batch generation support

3. **Category Checkers** (`src/categories/*.py`)
   - Each category is a separate module inheriting from `BaseChecker`
   - Uses category-specific prompts from `src/prompts.py`
   - Parses Claude API JSON responses into `MethodologicalIssue` objects
   - Independent execution enables parallel processing

4. **Data Models** (`src/models/*.py`)
   - Pydantic models for type safety and validation
   - `MethodologicalIssue`: Output data structure
   - `PaperData`: Input data structure (from Stage 1)
   - Automatic schema validation and serialization

### Error Handling

- **API Failures**: Retries with exponential backoff (configurable max retries)
- **Rate Limits**: Automatic backoff and retry
- **Partial Failures**: Returns successful results even if some categories fail
- **Invalid Input**: Pydantic validation raises clear error messages
- **Timeout Handling**: Configurable timeout per API call

### Performance

- **Parallel Execution**: 9 categories checked concurrently (default 4 workers)
- **Batch Processing**: ClaudeClient supports batch generation
- **Caching**: Response parsing is efficient with Pydantic models
- **Streaming**: Large papers processed in manageable chunks

## Known Limitations

1. **API Dependency**: Requires Anthropic API access and credits
2. **Rate Limits**: Heavy usage may hit API rate limits (handles gracefully)
3. **Detection Quality**: Accuracy depends on prompt engineering and Claude model capabilities
4. **False Positives**: Some issues may be flagged incorrectly (confidence scores help)
5. **Language Support**: Currently optimized for English papers only

## Contributing

When adding new category checkers or modifying existing ones:

1. Follow the `BaseChecker` pattern in `src/categories/base.py`
2. Add category-specific prompts to `src/prompts.py`
3. Create comprehensive unit tests in `tests/test_categories.py`
4. Add integration test cases to `tests/test_integration.py`
5. Update documentation and this README

## License

[Add your license here]

## Citation

If you use this tool in your research, please cite:

```bibtex
[Add citation here]
```

## Support

For issues, questions, or contributions:
- GitHub Issues: [Add repo URL]
- Documentation: See `docs/` directory
- API Reference: `docs/API.md`
- Category Details: `docs/CATEGORIES.md`

---

**Version:** 1.0.0
**Last Updated:** 2024-02-23
**Python Version:** 3.10+
**Status:** Production Ready ✅
