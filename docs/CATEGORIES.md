# Methodological Issue Categories

This document provides detailed descriptions of the **9 categories** of methodological issues that Stage 2 detects, along with detection criteria, examples, and severity guidelines.

---

## Table of Contents

1. [Claim-Evidence Gap](#1-claim-evidence-gap)
2. [Data Leakage](#2-data-leakage)
3. [Unfair Comparison](#3-unfair-comparison)
4. [Cherry Picking](#4-cherry-picking)
5. [Missing Ablation](#5-missing-ablation)
6. [Statistical Validity](#6-statistical-validity)
7. [Implicit Assumption](#7-implicit-assumption)
8. [Reproducibility](#8-reproducibility)
9. [Causal Overclaim](#9-causal-overclaim)

---

## 1. Claim-Evidence Gap

**Category ID**: `claim_evidence_gap`

### Description

Detects claims that lack sufficient supporting evidence or where evidence contradicts the claim. This includes quantitative claims without corresponding data, generalizations beyond experimental scope, and results misrepresented in claims.

### What We Look For

- ✗ Claims in abstract/introduction/conclusion lacking supporting evidence in results
- ✗ Quantitative claims (e.g., "improves by 20%") without corresponding experimental data
- ✗ Generalizations beyond what experiments actually demonstrate
- ✗ Results misrepresented or overstated in claims
- ✗ Missing statistical significance for claimed improvements
- ✗ Claims about causality without proper causal analysis

### Detection Criteria

| Evidence Strength | Confidence | Severity |
|------------------|------------|----------|
| Direct contradiction between claim and evidence | 0.8-1.0 | Critical |
| Quantitative claim with no data | 0.7-0.9 | Critical |
| Vague claim with insufficient detail | 0.5-0.7 | Warning |
| Minor overstatement | 0.4-0.6 | Info |

### Examples

#### Critical Issue

**Claim**: "Our method achieves state-of-the-art performance on all benchmarks."

**Evidence**: Table 1 shows the method ranks 3rd out of 5 on benchmark A, and benchmark B results are not reported.

**Why It's Critical**: Directly contradicts experimental evidence.

---

**Claim**: "AlphaOPT improves solution quality by 35% compared to existing methods."

**Evidence**: No table or figure shows a 35% improvement; Table 2 shows 12% improvement.

**Why It's Critical**: Quantitative claim not supported by data.

#### Warning Issue

**Claim**: "Our approach generalizes to all optimization problems."

**Evidence**: Only tested on 2 specific problem types (TSP and knapsack).

**Why It's a Warning**: Overgeneralizes from limited experimental scope.

### Severity Guidelines

- **Critical**: Direct contradiction, fabricated numbers, claims about all datasets when only tested on one
- **Warning**: Overgeneralization, missing statistical tests, vague claims needing qualification
- **Info**: Minor overstatements that could be clarified with additional wording

### Suggestions Provided

- "Add experimental validation for the claim in Section X"
- "Qualify the claim to match the experimental scope (e.g., 'on the tested benchmarks')"
- "Include statistical significance tests to support the improvement claim"
- "Remove or weaken the claim if evidence is insufficient"

---

## 2. Data Leakage

**Category ID**: `data_leakage`

### Description

Detects potential contamination between train/validation/test sets that would invalidate experimental results. This is one of the most critical methodological flaws, as data leakage fundamentally invalidates all experimental findings.

### What We Look For

- ✗ Test data used during model training or hyperparameter tuning
- ✗ Validation data contaminating training set
- ✗ Information from test set influencing model selection or design
- ✗ **Temporal leakage**: Future information used to predict past events
- ✗ Feature engineering using statistics from entire dataset (including test set)
- ✗ Cross-validation issues (data points appearing in both train and test)
- ✗ Pre-processing applied to combined data before splitting
- ✗ Missing clear description of train/validation/test split procedures

### Detection Criteria

| Evidence Strength | Confidence | Severity |
|------------------|------------|----------|
| Explicit test set used for training | 0.9-1.0 | Critical |
| Temporal order violated (future→past) | 0.8-0.95 | Critical |
| Unclear split procedure + suspicious results | 0.6-0.8 | Critical |
| Preprocessing before splitting | 0.5-0.7 | Warning |
| Missing split description | 0.4-0.6 | Warning |

### Examples

#### Critical Issue: Temporal Leakage

**Evidence**: "We collected VM performance data from 2019-2020 and split it into train and test sets..."

**Issue**: No specification of temporal ordering. Risk that 2020 data was used to train models predicting 2019 performance.

**Why It's Critical**: Temporal leakage allows models to "see the future," invalidating results.

---

#### Critical Issue: Preprocessing Before Split

**Evidence**: "We normalized all features using mean and standard deviation, then split the data 80/20."

**Issue**: Normalization statistics computed on entire dataset (including test set), leaking information.

**Why It's Critical**: Test set statistics leak into training, inflating performance.

---

#### Critical Issue: Hyperparameter Tuning on Test Set

**Evidence**: "We tuned hyperparameters to maximize performance, then evaluated on our test set."

**Issue**: Unclear if tuning used validation set or test set. If test set was used, it's no longer a valid test set.

**Why It's Critical**: Test set used for decisions during development, not a true hold-out.

### Severity Guidelines

- **Critical**: Clear temporal leakage, test set used for any training decisions, preprocessing stats from full dataset
- **Warning**: Unclear split procedure, missing details that raise suspicion, k-fold CV without proper isolation
- **Info**: Missing random seed, unclear if preprocessing was done correctly (but likely okay)

### Suggestions Provided

- "Clearly specify temporal split: train on 2019 data, test on 2020 data"
- "Ensure preprocessing (normalization, scaling) uses only training data statistics"
- "Describe exact split procedure with timestamps/dates to rule out temporal leakage"
- "Use separate validation set for hyperparameter tuning, never tune on test set"
- "Add explicit statement: 'Test set was held out and never used until final evaluation'"

### Known Test Case

**OR-R1 Paper** (tests/fixtures/or_r1_paper.json) contains data leakage:
- Train/test overlap: VMs appear in both sets
- Temporal leakage: Future data predicts past
- Testing on same VMs used for training

---

## 3. Unfair Comparison

**Category ID**: `unfair_comparison`

### Description

Detects unfair or misleading comparisons with baseline methods that make the proposed method appear better than it truly is. This includes comparing against outdated/weak baselines, using different experimental conditions, or cherry-picking metrics.

### What We Look For

- ✗ Comparing against outdated or weak baselines (e.g., 2015 methods in 2024)
- ✗ Different experimental conditions for proposed method vs. baselines
- ✗ Baselines not properly tuned or optimized
- ✗ Proposed method using more data, compute, or iterations than baselines
- ✗ Cherry-picking metrics that favor the proposed method
- ✗ Missing comparisons with recent state-of-the-art methods
- ✗ Different evaluation protocols for different methods
- ✗ Unfair advantages in implementation (e.g., more recent libraries, better hardware)

### Detection Criteria

| Evidence Strength | Confidence | Severity |
|------------------|------------|----------|
| All baselines >5 years old | 0.85-1.0 | Critical |
| Clear resource disparity (10x compute for proposed) | 0.8-0.95 | Critical |
| Missing recent SOTA methods | 0.6-0.8 | Warning |
| Different evaluation protocols | 0.7-0.9 | Critical |
| Unusual metric selection | 0.5-0.7 | Warning |

### Examples

#### Critical Issue: Outdated Baselines

**Evidence**: "We compare against Greedy-2015, Simulated Annealing-2015..." (Paper from 2024)

**Issue**: All baselines are 9 years old. Recent methods from 2021-2024 not included.

**Why It's Critical**: Makes proposed method appear better than it is by avoiding strong recent competitors.

---

#### Critical Issue: Resource Disparity

**Evidence**: "We trained our model for 1000 epochs on 8 GPUs. Baselines were trained for 100 epochs on 1 GPU following their original papers."

**Issue**: Proposed method gets 80x more compute than baselines.

**Why It's Critical**: Unfair comparison — baselines might match performance with equal resources.

---

#### Warning Issue: Missing SOTA

**Evidence**: Comparison includes methods from 2020-2022, but recent 2023-2024 methods published at major venues are omitted.

**Issue**: Missing most recent state-of-the-art.

**Why It's a Warning**: Could be an oversight, but raises suspicion that recent methods outperform the proposed approach.

### Severity Guidelines

- **Critical**: All baselines >5 years old, 5x+ resource disparity, clearly different evaluation protocols
- **Warning**: Some baselines old (3-5 years), missing some recent methods, potential tuning discrepancies
- **Info**: Minor protocol differences, slightly older baselines (1-2 years) when field moves slowly

### Suggestions Provided

- "Include comparisons with recent state-of-the-art methods from 2021-2024"
- "Ensure all methods use same computational budget (epochs, GPUs, time)"
- "Re-run baselines with proper hyperparameter tuning using modern libraries"
- "Justify baseline selection if older methods are intentionally chosen"
- "Add at least 2-3 recent competitive methods to establish true contribution"

### Known Test Case

**AlphaOPT Paper** (tests/fixtures/alphaotp_paper.json) contains unfair comparison:
- Compares against Greedy-2015 and Simulated Annealing-2015
- 8-year gap between baselines and proposed method
- Missing recent RL-based optimization methods

---

## 4. Cherry Picking

**Category ID**: `cherry_picking`

### Description

Detects selective reporting of favorable results while omitting unfavorable ones. This includes reporting only datasets where the method works well, showing only best runs, or omitting standard metrics where performance is weak.

### What We Look For

- ✗ Selective reporting of datasets where method works well
- ✗ Missing results on standard benchmarks where method likely performs poorly
- ✗ Reporting only favorable metrics while omitting standard metrics
- ✗ Showing only best runs or cherry-picked examples
- ✗ Incomplete ablation studies that hide negative results
- ✗ Selective reporting of experimental conditions
- ✗ Missing error bars or variance information to hide inconsistency
- ✗ Focusing on outlier cases rather than average performance
- ✗ Reporting results only for specific hyperparameter settings

### Detection Criteria

| Evidence Strength | Confidence | Severity |
|------------------|------------|----------|
| Standard benchmark missing + suspicious | 0.7-0.9 | Warning |
| Only "best run" reported, no variance | 0.6-0.8 | Warning |
| Unusual metrics, standard ones omitted | 0.65-0.85 | Warning |
| Subset of datasets, no explanation | 0.5-0.7 | Warning |

### Examples

#### Warning Issue: Missing Standard Benchmark

**Evidence**: Paper evaluates on custom Dataset-A and Dataset-B, but omits standard benchmark Dataset-C that all prior work uses.

**Issue**: Selective dataset reporting. Dataset-C might show poor performance.

**Why It's a Warning**: Raises suspicion of cherry-picking, though could have legitimate reasons.

---

#### Warning Issue: No Variance Reported

**Evidence**: "We report the best run over 10 trials: Accuracy = 95.3%"

**Issue**: Only best result shown, no mean/std. Could be hiding high variance.

**Why It's a Warning**: Best-case results mislead readers about typical performance.

---

#### Warning Issue: Unusual Metrics

**Evidence**: Paper reports "adjusted F1 score" and "custom accuracy," omitting standard precision/recall.

**Issue**: Non-standard metrics without reporting standard ones raises suspicion.

**Why It's a Warning**: Custom metrics may be designed to favor the proposed method.

### Severity Guidelines

- **Critical**: Rarely assigned to cherry-picking (usually warning-level)
- **Warning**: Missing standard benchmarks, no variance reported, selective metric reporting, "best run" results
- **Info**: Minor metric omissions, small dataset selection with justification

### Suggestions Provided

- "Include results on standard benchmark Dataset-C to enable fair comparison"
- "Report mean ± std over multiple runs instead of best-case result"
- "Add standard metrics (precision, recall, F1) alongside custom metrics"
- "Explain why certain datasets or conditions were excluded"
- "Include error bars or confidence intervals in all result tables"

---

## 5. Missing Ablation

**Category ID**: `missing_ablation`

### Description

Detects insufficient ablation studies to validate design choices and claimed contributions. Good papers isolate each component/design choice and show its impact through controlled experiments.

### What We Look For

- ✗ Novel components introduced without ablation to show their impact
- ✗ Multiple design choices made without justification through ablations
- ✗ Claimed contributions not validated by removing them
- ✗ Missing component-wise analysis of proposed method
- ✗ Lack of sensitivity analysis for hyperparameters
- ✗ Missing comparison of design alternatives
- ✗ No analysis of which parts of the method contribute to performance
- ✗ Complex methods without breakdown of component contributions

### Detection Criteria

| Evidence Strength | Confidence | Severity |
|------------------|------------|----------|
| Main contribution not ablated | 0.75-0.95 | Warning |
| 3+ components, no ablation table | 0.7-0.9 | Warning |
| Minor component not ablated | 0.5-0.7 | Info |
| Ablation present but incomplete | 0.4-0.6 | Info |

### Examples

#### Warning Issue: Main Contribution Not Ablated

**Evidence**: "Our key contribution is the attention-based routing module. Results in Table 2 show our full method achieves 92% accuracy."

**Issue**: No ablation comparing (full method) vs. (method without attention routing).

**Why It's a Warning**: Cannot validate that the claimed contribution actually helps.

---

#### Warning Issue: Multi-Component Method, No Breakdown

**Evidence**: Method has 4 novel components (A, B, C, D), but only reports full method results.

**Issue**: No ablation table showing A, A+B, A+B+C, A+B+C+D.

**Why It's a Warning**: Cannot tell which components contribute to performance; some might be unnecessary.

---

#### Info Issue: Incomplete Ablation

**Evidence**: Ablation table shows (Full) vs. (No Component A) vs. (No Component B), but doesn't test (No A, No B) or alternative designs.

**Issue**: Ablation is present but could be more comprehensive.

**Why It's Info**: Partial ablation is provided; just suggesting improvements.

### Severity Guidelines

- **Critical**: Rarely assigned (usually warning)
- **Warning**: Main contribution not ablated, multi-component method with no breakdown, no sensitivity analysis
- **Info**: Minor components not ablated, ablation present but incomplete

### Suggestions Provided

- "Add ablation study showing performance with and without the attention-based routing module"
- "Include component-wise ablation table: A, A+B, A+B+C, Full"
- "Provide statistical significance tests for each component's contribution"
- "Analyze which components contribute most to performance improvements"
- "Include sensitivity analysis for key hyperparameters"

---

## 6. Statistical Validity

**Category ID**: `statistical_validity`

### Description

Detects statistical issues like missing significance tests, small sample sizes, or invalid statistical conclusions. Proper statistical rigor requires reporting variance, testing significance, and avoiding p-hacking.

### What We Look For

- ✗ Claims of improvement without significance tests
- ✗ Missing error bars, standard deviations, or confidence intervals
- ✗ Small sample sizes without acknowledging limitations
- ✗ Multiple comparisons without correction (p-hacking risk)
- ✗ Invalid statistical tests for the data type
- ✗ Confusing correlation with causation
- ✗ Cherry-picking significance level after seeing results
- ✗ Missing information about number of runs or trials
- ✗ Comparing means without considering variance
- ✗ Claims based on single runs without replication

### Detection Criteria

| Evidence Strength | Confidence | Severity |
|------------------|------------|----------|
| No significance test for main claim | 0.7-0.9 | Warning |
| Single run, no variance | 0.65-0.85 | Warning |
| Small sample (n<30) without acknowledgment | 0.6-0.8 | Warning |
| No error bars in any results | 0.7-0.9 | Warning |
| Multiple testing without correction | 0.5-0.7 | Info |

### Examples

#### Warning Issue: No Significance Test

**Evidence**: "Our method achieves 87.3% accuracy compared to 85.1% for the baseline."

**Issue**: 2.2% improvement reported, but no significance test. Difference could be within noise.

**Why It's a Warning**: Cannot tell if improvement is real or random variation.

---

#### Warning Issue: No Variance Reported

**Evidence**: All results reported as single numbers (e.g., "Accuracy: 92.1") with no ± std.

**Issue**: No indication of variance across runs.

**Why It's a Warning**: Could be hiding high variance or cherry-picked runs.

---

#### Warning Issue: Small Sample Size

**Evidence**: "We tested on 15 examples and achieved 93% success rate."

**Issue**: n=15 is very small; results may not generalize.

**Why It's a Warning**: Small sample limits statistical power and generalizability.

### Severity Guidelines

- **Critical**: Rarely assigned (usually warning)
- **Warning**: No significance tests for main claims, no variance reported, very small samples (n<10)
- **Info**: Missing significance for minor claims, moderate sample sizes (30-100), missing details about test type

### Suggestions Provided

- "Add statistical significance test (e.g., t-test, Wilcoxon) to verify improvement is not due to chance"
- "Report mean ± standard deviation over multiple runs (at least 5-10 runs)"
- "Include confidence intervals (95% CI) for main results"
- "Acknowledge small sample size and discuss limitations on generalizability"
- "Apply multiple testing correction (Bonferroni, FDR) when comparing across many conditions"

---

## 7. Implicit Assumption

**Category ID**: `implicit_assumption`

### Description

Detects unstated assumptions that may not hold in practice, such as assumptions about data distribution, problem structure, deployment conditions, or resource availability. Good papers explicitly state and justify their assumptions.

### What We Look For

- ✗ Unstated assumptions about data distribution (IID, stationarity)
- ✗ Assumptions about problem structure not validated
- ✗ Implicit assumptions about deployment conditions
- ✗ Assumptions about user behavior or requirements
- ✗ Unstated computational or resource assumptions
- ✗ Assumptions about generalization not tested
- ✗ Implicit assumptions in problem formulation
- ✗ Assumptions about access to certain information
- ✗ Idealized conditions assumed without discussion

### Detection Criteria

| Evidence Strength | Confidence | Severity |
|------------------|------------|----------|
| Critical assumption unstated (IID, stationarity) | 0.6-0.8 | Warning |
| Deployment gap (lab vs. real-world) | 0.55-0.75 | Warning |
| Resource assumptions (unlimited compute) | 0.5-0.7 | Info |
| Minor assumptions | 0.4-0.6 | Info |

### Examples

#### Warning Issue: IID Assumption Not Stated

**Evidence**: Method trains on Dataset-A and tests on Dataset-B (different domain).

**Issue**: Assumes IID (independent, identically distributed) data, but datasets are from different domains.

**Why It's a Warning**: IID assumption likely violated; method may not generalize.

---

#### Warning Issue: Real-Time Requirement Ignored

**Evidence**: Method requires 30 seconds per prediction, paper applies it to fraud detection.

**Issue**: Fraud detection requires real-time decisions (<1 second), but latency not discussed.

**Why It's a Warning**: Implicit assumption that latency doesn't matter contradicts real-world deployment.

---

#### Info Issue: Perfect Labels Assumed

**Evidence**: Method assumes training labels are 100% correct.

**Issue**: Real-world labels often have noise, but this isn't discussed.

**Why It's Info**: Common assumption, but worth stating and validating robustness to label noise.

### Severity Guidelines

- **Critical**: Rarely assigned (usually warning)
- **Warning**: Critical assumptions unstated (IID, stationarity, temporal order), significant deployment gap
- **Info**: Minor assumptions, common idealizations (perfect labels, no noise)

### Suggestions Provided

- "Explicitly state assumption that data is IID and validate this on the test set"
- "Discuss gap between experimental setup (batch processing) and deployment (real-time requirements)"
- "Acknowledge assumption of perfect labels and test robustness to label noise"
- "Validate that method works under realistic conditions (noisy data, limited compute)"

---

## 8. Reproducibility

**Category ID**: `reproducibility`

### Description

Detects missing information needed to reproduce the work. Reproducible papers provide complete implementation details, hyperparameters, datasets, code, and evaluation protocols.

### What We Look For

- ✗ Missing implementation details
- ✗ Hyperparameters not specified
- ✗ Random seeds not mentioned
- ✗ Dataset details incomplete (version, split, preprocessing)
- ✗ Training procedures not fully described
- ✗ Computational requirements not stated (GPU, training time)
- ✗ Code availability not mentioned
- ✗ Missing architectural details (layer sizes, activations)
- ✗ Evaluation protocol not fully specified
- ✗ Dependencies and library versions not listed

### Detection Criteria

| Evidence Strength | Confidence | Severity |
|------------------|------------|----------|
| No hyperparameters specified | 0.7-0.9 | Warning |
| No code/data availability statement | 0.6-0.8 | Warning |
| Missing critical architectural details | 0.65-0.85 | Warning |
| Missing random seeds | 0.5-0.7 | Info |
| Missing library versions | 0.4-0.6 | Info |

### Examples

#### Warning Issue: No Hyperparameters

**Evidence**: "We trained a neural network..." (no learning rate, batch size, optimizer, etc.)

**Issue**: Cannot reproduce training without hyperparameters.

**Why It's a Warning**: Essential details missing.

---

#### Warning Issue: No Code Availability

**Evidence**: Paper makes no mention of code, data, or model release.

**Issue**: Readers cannot reproduce without implementation details.

**Why It's a Warning**: Reduces reproducibility significantly.

---

#### Info Issue: No Random Seed

**Evidence**: Experiments report results over multiple runs, but random seed not specified.

**Issue**: Exact results cannot be reproduced.

**Why It's Info**: Minor issue — readers can approximate results even without exact seed.

### Severity Guidelines

- **Critical**: Rarely assigned (usually warning)
- **Warning**: No hyperparameters, no code/data availability, missing architectural details, incomplete training procedure
- **Info**: Missing random seeds, library versions, hardware details

### Suggestions Provided

- "Specify all hyperparameters: learning rate, batch size, optimizer, epochs, etc."
- "Provide code repository (GitHub) or promise to release code upon acceptance"
- "Include complete model architecture: layer types, sizes, activation functions"
- "Specify dataset version, split procedure, and preprocessing steps"
- "Report training time and hardware used (GPU model, memory)"

---

## 9. Causal Overclaim

**Category ID**: `causal_overclaim`

### Description

Detects causal claims not supported by experimental design. Causal language (causes, leads to, because, due to) requires causal evidence (controlled experiments, ablations), not just correlations.

### What We Look For

- ✗ Causal language (causes, leads to, because, due to) without causal evidence
- ✗ Correlation presented as causation
- ✗ Claims about mechanisms without proper validation
- ✗ Explanations of "why" without controlled experiments
- ✗ Claims that X causes Y based only on observational data
- ✗ Causal interpretations of neural network components without proper analysis
- ✗ Claiming feature importance implies causality
- ✗ Missing confounding variable consideration
- ✗ Reverse causality not ruled out

### Detection Criteria

| Evidence Strength | Confidence | Severity |
|------------------|------------|----------|
| Strong causal language, no controlled exp | 0.7-0.9 | Warning |
| "X causes Y" from correlation | 0.75-0.95 | Warning |
| Mechanism claim without ablation | 0.6-0.8 | Info |
| Weak causal language | 0.4-0.6 | Info |

### Examples

#### Warning Issue: Correlation as Causation

**Evidence**: "We found that attention weights correlate with performance (r=0.7), therefore attention causes better performance."

**Issue**: Correlation does not imply causation. Both could be caused by a third factor.

**Why It's a Warning**: Causal claim without causal evidence.

---

#### Warning Issue: Mechanism Claim Without Validation

**Evidence**: "The gating mechanism improves performance because it filters out irrelevant features."

**Issue**: "Because" implies causal mechanism, but no ablation validates this explanation.

**Why It's a Warning**: Mechanism not validated — could be wrong explanation.

---

#### Info Issue: Weak Causal Language

**Evidence**: "We believe the attention module leads to better representations..."

**Issue**: "Leads to" is causal language, but claim is hedged with "we believe."

**Why It's Info**: Weak causal claim; could be strengthened with ablation evidence.

### Severity Guidelines

- **Critical**: Rarely assigned (usually warning)
- **Warning**: Strong causal claims without controlled experiments, correlation presented as causation
- **Info**: Weak causal language, speculative mechanisms, missing confounding consideration

### Suggestions Provided

- "Replace causal language ('causes', 'because') with correlational language ('associated with', 'correlated with') unless causal evidence is provided"
- "Add ablation study to validate that X causes Y (e.g., remove X and show Y decreases)"
- "Include controlled experiment to rule out confounding variables"
- "Provide mechanistic validation through intervention studies or theoretical analysis"
- "Acknowledge that observed correlation does not imply causation"

---

## Category Selection Guidelines

### For Stage 3 UI: How to Display Categories

**Group by Severity:**
```
🔴 Critical Issues (2)
  - Data Leakage: Train/test overlap detected
  - Unfair Comparison: Outdated baselines from 2015

⚠️  Warnings (3)
  - Missing Ablation: Key component not ablated
  - Statistical Validity: No significance tests reported
  - Claim-Evidence Gap: Quantitative claim lacks data

ℹ️  Info (1)
  - Reproducibility: Random seed not specified
```

**Group by Category:**
```
Experimental Rigor
  - Data Leakage (critical)
  - Unfair Comparison (critical)
  - Cherry Picking (warning)

Claims & Evidence
  - Claim-Evidence Gap (warning)
  - Causal Overclaim (info)

Statistical Issues
  - Statistical Validity (warning)
  - Missing Ablation (warning)

Transparency
  - Reproducibility (info)
  - Implicit Assumption (info)
```

### Category Overlap

Some issues may span multiple categories:

- **Data leakage + Unfair comparison**: Using more data for proposed method than baselines
- **Cherry picking + Statistical validity**: Reporting best run without variance
- **Claim-evidence gap + Causal overclaim**: Causal claim without supporting evidence
- **Missing ablation + Claim-evidence gap**: Contribution claimed but not validated

Stage 2 may report the same issue under multiple categories if it fits multiple definitions. Stage 3 should deduplicate or merge overlapping issues in the UI.

---

## References

- **Prompts**: See `src/prompts.py` for full category-specific prompts sent to Claude
- **Models**: See `src/models/issue.py` for `MethodologicalIssue` schema
- **Checkers**: See `src/categories/` for individual category checker implementations
- **Tests**: See `tests/test_categories.py` and `tests/test_integration.py` for test cases

---

## Appendix: Detection Examples by Category

### AlphaOPT Paper (Known Test Case)

**Expected Detection**: `unfair_comparison` (critical)

**Evidence**:
- Section "Experimental Results" compares against "Greedy-2015" and "Simulated Annealing-2015"
- Paper is from 2023, baselines are 8 years old
- Missing recent RL-based optimization methods (2019-2023)

**Expected Issue**:
```json
{
  "category": "unfair_comparison",
  "severity": "critical",
  "confidence": 0.92,
  "title": "Comparison against outdated baselines from 2015",
  "description": "The paper compares the proposed AlphaOPT method (2023) exclusively against baseline methods from 2015...",
  "evidence": {
    "section": "Experimental Results",
    "quote": "We compare our method against Greedy-2015 and Simulated Annealing-2015...",
    "table_reference": "Table 1"
  },
  "suggestions": [
    "Include comparisons with recent state-of-the-art methods from 2021-2023",
    "Justify the choice of baselines if older methods are intentionally used"
  ]
}
```

### OR-R1 Paper (Known Test Case)

**Expected Detection**: `data_leakage` (critical)

**Evidence**:
- Section "Experimental Setup" describes train/test split but lacks temporal ordering
- VMs appear in both train and test sets
- Future data (2020) used to predict past (2019)

**Expected Issue**:
```json
{
  "category": "data_leakage",
  "severity": "critical",
  "confidence": 0.88,
  "title": "Temporal leakage in time-series experiment",
  "description": "The paper describes testing on VM performance data from 2019-2020, but the train/test split procedure is not clearly specified...",
  "evidence": {
    "section": "Experimental Setup",
    "quote": "We collected VM performance data spanning 2019-2020 and split it into train and test sets...",
    "page": 6
  },
  "suggestions": [
    "Clearly specify the temporal split: train on 2019 data, test on 2020 data",
    "Ensure no future information leaks into past predictions"
  ]
}
```

---

**Last Updated**: 2026-02-23
**Version**: 0.1.0
