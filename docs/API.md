# Stage 2 API Contract

This document defines the API contract for **Stage 2: Logic & Methodology Verification** in the Paper Verifier pipeline.

## Overview

**Stage 2** receives structured paper data from **Stage 1** (PDF extraction & parsing) and outputs a list of detected methodological issues to **Stage 3** (report generation & UI).

```
┌─────────┐      PaperData JSON       ┌─────────┐      Issues JSON      ┌─────────┐
│ Stage 1 │ ─────────────────────────> │ Stage 2 │ ────────────────────> │ Stage 3 │
│  (PDF)  │                            │ (Logic) │                       │  (UI)   │
└─────────┘                            └─────────┘                       └─────────┘
```

**Key Principle**: Stage 2 runs independently of Stage 3 (parallel execution design), meaning both stages can process data simultaneously in a streaming architecture.

---

## Input Format: PaperData (from Stage 1)

Stage 2 expects a JSON object conforming to the `PaperData` Pydantic model.

### PaperData Schema

```json
{
  "metadata": {
    "title": "string (optional)",
    "authors": ["string"],
    "year": "integer (optional)",
    "venue": "string (optional)",
    "doi": "string (optional)",
    "arxiv_id": "string (optional)"
  },
  "abstract": "string (optional)",
  "sections": [
    {
      "title": "string (required)",
      "content": "string (required)",
      "page": "integer (optional)",
      "subsections": [
        {
          "title": "string",
          "content": "string",
          "page": "integer (optional)",
          "subsections": []
        }
      ]
    }
  ],
  "tables": [
    {
      "id": "string (required, e.g., 'Table 1', 'Figure 3')",
      "caption": "string (optional)",
      "content": "string (optional, text representation)",
      "data": "object (optional, structured data)",
      "page": "integer (optional)"
    }
  ],
  "claims": [
    {
      "text": "string (required)",
      "section": "string (optional)",
      "claim_type": "string (optional, e.g., 'main_contribution', 'result', 'comparison')",
      "supporting_evidence": ["string"]
    }
  ],
  "experiments": [
    {
      "name": "string (optional)",
      "dataset": "string (optional)",
      "metrics": ["string"],
      "baselines": ["string"],
      "results": "object (optional)"
    }
  ],
  "references": ["string"],
  "full_text": "string (optional)"
}
```

### Field Descriptions

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `metadata` | Metadata | Yes | Paper metadata (title, authors, year, venue, DOI, arXiv ID) |
| `metadata.title` | string | No | Full paper title |
| `metadata.authors` | string[] | No | List of author names |
| `metadata.year` | integer | No | Publication year |
| `metadata.venue` | string | No | Publication venue (conference/journal name) |
| `metadata.doi` | string | No | Digital Object Identifier |
| `metadata.arxiv_id` | string | No | arXiv identifier (e.g., "2301.12345") |
| `abstract` | string | No | Paper abstract/summary |
| `sections` | PaperSection[] | No | Hierarchical sections of the paper |
| `sections[].title` | string | Yes | Section title (e.g., "Introduction", "Methods") |
| `sections[].content` | string | Yes | Full text content of the section |
| `sections[].page` | integer | No | Page number where section starts |
| `sections[].subsections` | PaperSection[] | No | Nested subsections (recursive structure) |
| `tables` | Table[] | No | Tables and figures extracted from paper |
| `tables[].id` | string | Yes | Identifier (e.g., "Table 1", "Figure 3") |
| `tables[].caption` | string | No | Caption or title |
| `tables[].content` | string | No | Text representation of table content |
| `tables[].data` | object | No | Structured data (if parseable) |
| `tables[].page` | integer | No | Page number |
| `claims` | Claim[] | No | Key claims extracted from the paper |
| `claims[].text` | string | Yes | The claim text |
| `claims[].section` | string | No | Section where claim appears |
| `claims[].claim_type` | string | No | Type: "main_contribution", "result", "comparison", etc. |
| `claims[].supporting_evidence` | string[] | No | References to supporting evidence |
| `experiments` | Experiment[] | No | Experiments and evaluations described |
| `experiments[].name` | string | No | Experiment name/description |
| `experiments[].dataset` | string | No | Dataset name |
| `experiments[].metrics` | string[] | No | Evaluation metrics used |
| `experiments[].baselines` | string[] | No | Baseline methods compared against |
| `experiments[].results` | object | No | Experimental results |
| `references` | string[] | No | List of citations/references |
| `full_text` | string | No | Complete paper text (if available) |

### Example Input (Minimal)

```json
{
  "metadata": {
    "title": "AlphaOPT: Reinforcement Learning for Optimization",
    "authors": ["John Doe", "Jane Smith"],
    "year": 2023,
    "venue": "NeurIPS"
  },
  "abstract": "We present AlphaOPT, a novel approach using RL for combinatorial optimization...",
  "sections": [
    {
      "title": "Introduction",
      "content": "Optimization problems are ubiquitous in many domains...",
      "page": 1
    },
    {
      "title": "Experimental Results",
      "content": "We evaluate AlphaOPT on standard benchmarks and compare against baselines from 2015...",
      "page": 5
    }
  ],
  "tables": [
    {
      "id": "Table 1",
      "caption": "Comparison with baselines",
      "content": "Method | Accuracy | Time\nAlphaOPT | 95% | 10s\nBaseline-2015 | 85% | 15s",
      "page": 5
    }
  ],
  "experiments": [
    {
      "name": "TSP Benchmark",
      "dataset": "TSP-100",
      "metrics": ["accuracy", "runtime"],
      "baselines": ["Greedy-2015", "Simulated Annealing-2015"]
    }
  ]
}
```

---

## Output Format: MethodologicalIssue[] (to Stage 3)

Stage 2 outputs a JSON array of detected methodological issues, each conforming to the `MethodologicalIssue` Pydantic model.

### Output Schema

```json
{
  "issues": [
    {
      "category": "string (required, one of 9 categories)",
      "severity": "string (required, one of: critical, warning, info)",
      "confidence": "number (required, 0.0 to 1.0)",
      "title": "string (required)",
      "description": "string (required)",
      "evidence": {
        "section": "string (optional)",
        "quote": "string (optional)",
        "table_reference": "string (optional)",
        "page": "integer (optional)"
      },
      "suggestions": ["string"]
    }
  ],
  "metadata": {
    "total_categories": "integer",
    "successful_categories": "integer",
    "failed_categories": ["string"],
    "is_partial": "boolean",
    "success_rate": "number (0.0 to 1.0)"
  }
}
```

### Field Descriptions

| Field | Type | Required | Constraints | Description |
|-------|------|----------|-------------|-------------|
| `issues` | MethodologicalIssue[] | Yes | - | Array of all detected issues |
| `issues[].category` | string | Yes | One of 9 categories* | Category name (see Categories section) |
| `issues[].severity` | string (enum) | Yes | `critical`, `warning`, or `info` | Severity level of the issue |
| `issues[].confidence` | number | Yes | 0.0 ≤ confidence ≤ 1.0 | Detector confidence score |
| `issues[].title` | string | Yes | - | Short title (1-2 sentences) |
| `issues[].description` | string | Yes | - | Detailed explanation of the issue |
| `issues[].evidence` | Evidence | Yes | - | Supporting evidence |
| `issues[].evidence.section` | string | No | - | Section name where issue found |
| `issues[].evidence.quote` | string | No | - | Direct quote demonstrating issue |
| `issues[].evidence.table_reference` | string | No | - | Table/figure reference (e.g., "Table 2") |
| `issues[].evidence.page` | integer | No | - | Page number |
| `issues[].suggestions` | string[] | No | - | Actionable recommendations |
| `metadata` | object | Yes | - | Analysis metadata |
| `metadata.total_categories` | integer | Yes | - | Total categories checked (9) |
| `metadata.successful_categories` | integer | Yes | - | Categories that completed successfully |
| `metadata.failed_categories` | string[] | Yes | - | Categories that failed (partial failure handling) |
| `metadata.is_partial` | boolean | Yes | - | True if some categories failed |
| `metadata.success_rate` | number | Yes | 0.0 to 1.0 | Fraction of successful categories |

\* **9 Valid Categories**: `claim_evidence_gap`, `data_leakage`, `unfair_comparison`, `cherry_picking`, `missing_ablation`, `statistical_validity`, `implicit_assumption`, `reproducibility`, `causal_overclaim`

### Severity Levels

| Severity | Meaning | Example |
|----------|---------|---------|
| `critical` | Fundamental flaw that invalidates results | Data leakage, unfair comparison with outdated baselines |
| `warning` | Significant concern that weakens claims | Missing ablation study, no statistical significance tests |
| `info` | Minor issue or best practice recommendation | Missing hyperparameter details, unclear notation |

### Confidence Scores

- **0.9 - 1.0**: High confidence (clear evidence, unambiguous issue)
- **0.7 - 0.9**: Medium-high confidence (strong evidence, likely issue)
- **0.5 - 0.7**: Medium confidence (reasonable evidence, possible issue)
- **0.0 - 0.5**: Low confidence (weak evidence, uncertain issue)

### Example Output

```json
{
  "issues": [
    {
      "category": "unfair_comparison",
      "severity": "critical",
      "confidence": 0.92,
      "title": "Comparison against outdated baselines from 2015",
      "description": "The paper compares the proposed AlphaOPT method (2023) exclusively against baseline methods from 2015, which are 8 years old. This creates an unfair comparison as significant advances have been made in the field since 2015. Recent state-of-the-art methods from 2021-2023 are not included in the comparison.",
      "evidence": {
        "section": "Experimental Results",
        "quote": "We compare our method against Greedy-2015 and Simulated Annealing-2015...",
        "table_reference": "Table 1",
        "page": 5
      },
      "suggestions": [
        "Include comparisons with recent state-of-the-art methods from 2021-2023",
        "Justify the choice of baselines if older methods are intentionally used",
        "Acknowledge the limitation of comparing only against 2015 baselines",
        "Add at least 2-3 recent methods (2021+) to establish competitive performance"
      ]
    },
    {
      "category": "data_leakage",
      "severity": "critical",
      "confidence": 0.88,
      "title": "Potential temporal leakage in time-series experiment",
      "description": "The paper describes testing on VM performance data from 2019-2020, but the train/test split procedure is not clearly specified. There is a risk that future information (e.g., 2020 data) was used to train models that predict 2019 performance, which would constitute temporal leakage.",
      "evidence": {
        "section": "Experimental Setup",
        "quote": "We collected VM performance data spanning 2019-2020 and split it into train and test sets...",
        "page": 6
      },
      "suggestions": [
        "Clearly specify the temporal split: train on 2019 data, test on 2020 data",
        "Ensure no future information leaks into past predictions",
        "Describe the exact split procedure with dates/timestamps",
        "Validate that preprocessing was done only on training data before splitting"
      ]
    }
  ],
  "metadata": {
    "total_categories": 9,
    "successful_categories": 9,
    "failed_categories": [],
    "is_partial": false,
    "success_rate": 1.0
  }
}
```

---

## Partial Failure Handling

Stage 2 implements **graceful degradation** — if some category checkers fail (e.g., due to API rate limits, timeouts, or errors), partial results are still returned:

```json
{
  "issues": [
    {
      "category": "data_leakage",
      "severity": "critical",
      "confidence": 0.85,
      "title": "Train/test overlap detected",
      "description": "..."
    }
  ],
  "metadata": {
    "total_categories": 9,
    "successful_categories": 7,
    "failed_categories": ["statistical_validity", "reproducibility"],
    "is_partial": true,
    "success_rate": 0.778
  }
}
```

**Stage 3** should check `metadata.is_partial` and display a warning if `true`, informing users that some checks were incomplete.

---

## API Guarantees

### What Stage 2 Guarantees

1. ✅ **Valid JSON output**: Always returns valid JSON conforming to the output schema
2. ✅ **Partial results on failure**: Returns issues from successful categories even if some fail
3. ✅ **Category validation**: All `category` fields are one of the 9 valid categories
4. ✅ **Confidence bounds**: All `confidence` scores are in range [0.0, 1.0]
5. ✅ **Severity validation**: All `severity` fields are `critical`, `warning`, or `info`
6. ✅ **Evidence references**: At least one evidence field (section, quote, or table_reference) is populated per issue
7. ✅ **Actionable suggestions**: Each issue includes at least one suggestion

### What Stage 2 Does NOT Guarantee

1. ❌ **Issue detection completeness**: May miss issues (false negatives) — detection quality depends on Claude API
2. ❌ **Zero false positives**: May flag non-issues (false positives) — confidence scores indicate certainty
3. ❌ **Consistent issue count**: Same paper may yield different issues on different runs (LLM variability)
4. ❌ **Full category coverage**: Some categories may fail (see partial failure handling)
5. ❌ **Execution time guarantees**: Analysis time varies based on paper length and API latency

---

## Error Handling

### HTTP Status Codes (if exposed as REST API)

| Code | Meaning | Response |
|------|---------|----------|
| 200 | Success | Full results with all categories |
| 206 | Partial Content | Partial results (some categories failed) |
| 400 | Bad Request | Invalid input JSON schema |
| 422 | Unprocessable Entity | Valid JSON but invalid PaperData model |
| 429 | Too Many Requests | Claude API rate limit exceeded |
| 500 | Internal Server Error | Unexpected error |
| 503 | Service Unavailable | Claude API unavailable |

### CLI Exit Codes

| Code | Meaning |
|------|---------|
| 0 | Success (full or partial results) |
| 1 | Error (invalid input, file not found, etc.) |
| 130 | User interrupt (SIGINT / Ctrl+C) |

### Error Response Format

```json
{
  "error": {
    "type": "ValidationError",
    "message": "Invalid PaperData schema: Field 'sections[0].title' is required",
    "details": {
      "field": "sections[0].title",
      "constraint": "required"
    }
  }
}
```

---

## Usage Examples

### Python API

```python
from src.logic_checker import LogicChecker
from src.claude_client import ClaudeClient
from src.models.paper_data import PaperData
import json

# Load input from Stage 1
with open("stage1_output.json") as f:
    paper_dict = json.load(f)
    paper_data = PaperData(**paper_dict)  # Validates schema

# Initialize checker
client = ClaudeClient(api_key="sk-ant-...")
checker = LogicChecker(client)

# Run analysis
result = checker.check_all(paper_data)

# Output to Stage 3
output = result.to_dict()
with open("stage2_output.json", "w") as f:
    json.dump(output, f, indent=2)

# Check for partial failures
if result.is_partial:
    print(f"Warning: {len(result.failed_categories)} categories failed")
    print(f"Failed categories: {', '.join(result.failed_categories)}")
```

### CLI

```bash
# Process Stage 1 output
python -m src.main stage1_output.json --output stage2_output.json

# Handle partial failures
if [ $? -eq 0 ]; then
  # Check if output contains partial results
  if grep -q '"is_partial": true' stage2_output.json; then
    echo "Warning: Partial results (some categories failed)"
  fi
  # Forward to Stage 3
  cat stage2_output.json | stage3_processor
fi
```

---

## Integration Testing

### Known Test Cases

Stage 2 includes integration tests with known papers:

1. **AlphaOPT Paper** (tests/fixtures/alphaotp_paper.json)
   - Expected detection: `unfair_comparison` (critical severity)
   - Issue: Compares against outdated 2015 baselines

2. **OR-R1 Paper** (tests/fixtures/or_r1_paper.json)
   - Expected detection: `data_leakage` (critical severity)
   - Issue: Train/test overlap, temporal leakage

### Validation Commands

```bash
# Run integration tests
pytest tests/test_integration.py -v

# Test with known papers
python -m src.main tests/fixtures/alphaotp_paper.json
python -m src.main tests/fixtures/or_r1_paper.json
```

---

## Performance Characteristics

| Metric | Typical Value | Notes |
|--------|---------------|-------|
| **Latency** | 30-90 seconds | Varies with paper length and Claude API latency |
| **Throughput** | 1-2 papers/minute | With parallel execution (4 workers) |
| **API Calls** | 9 per paper | One per category (parallelized) |
| **Token Usage** | 50k-200k tokens | Depends on paper length |
| **Memory** | <500 MB | Small to medium papers |

**Optimization**: For high-throughput scenarios, run Stage 2 and Stage 3 in parallel (streaming architecture).

---

## Versioning

**Current Version**: `0.1.0`

**Schema Versioning**: Future changes will follow semantic versioning:
- **Patch** (0.1.x): Bug fixes, no schema changes
- **Minor** (0.x.0): Backward-compatible additions (new optional fields)
- **Major** (x.0.0): Breaking schema changes (field removals, type changes)

**Compatibility**: Stage 3 must support Stage 2 output versions within the same major version.

---

## References

- **Pydantic Models**: `src/models/paper_data.py`, `src/models/issue.py`
- **Category Prompts**: `src/prompts.py`
- **Logic Checker**: `src/logic_checker.py`
- **Test Fixtures**: `tests/fixtures/`
- **Integration Tests**: `tests/test_integration.py`

---

## Change Log

| Version | Date | Changes |
|---------|------|---------|
| 0.1.0 | 2026-02-23 | Initial API contract definition |

---

**For detailed category descriptions, see [`CATEGORIES.md`](./CATEGORIES.md).**
