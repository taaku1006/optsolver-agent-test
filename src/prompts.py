"""Category-specific prompts for methodological issue detection.

Each prompt instructs Claude to analyze a paper for a specific type of
methodological issue and return structured findings with severity, confidence,
evidence, and actionable suggestions.
"""

# System prompt template used across all categories
SYSTEM_PROMPT_TEMPLATE = """You are an expert peer reviewer analyzing research papers for methodological issues.
Your task is to carefully examine the provided paper data and identify potential {category_name} issues.

For each issue found, provide:
1. A severity level (critical, warning, or info)
2. A confidence score (0.0 to 1.0)
3. Specific evidence (section, quote, or table reference)
4. Actionable suggestions for improvement

Be thorough but fair. Only report issues you have reasonable confidence in.
Focus on substantive methodological concerns, not minor stylistic issues.

Return your analysis as a JSON array of issues, where each issue has:
- title: Short descriptive title
- description: Detailed explanation of the issue
- severity: "critical", "warning", or "info"
- confidence: Float between 0.0 and 1.0
- evidence_section: Section name where issue was found
- evidence_quote: Relevant quote from the paper (if applicable)
- evidence_table: Table reference (if applicable)
- suggestions: Array of actionable improvement suggestions

If no issues are found, return an empty array []."""


CATEGORY_PROMPTS = {
    "claim_evidence_gap": {
        "name": "Claim-Evidence Gap",
        "description": "Detects claims that lack sufficient supporting evidence or where evidence contradicts claims",
        "system_prompt": SYSTEM_PROMPT_TEMPLATE.format(category_name="claim-evidence gap"),
        "user_prompt_template": """Analyze this paper for claim-evidence gaps.

Look for:
- Claims in the abstract, introduction, or conclusion that lack supporting evidence in results
- Quantitative claims without corresponding experimental data
- Generalizations beyond what the experiments actually demonstrate
- Results misrepresented or overstated in claims
- Missing statistical significance for claimed improvements
- Claims about causality without proper causal analysis

Paper Data:
{paper_data}

Focus especially on:
- Main contributions claimed in abstract/introduction vs. actual experimental validation
- Performance claims vs. tables/figures showing results
- Generalization claims vs. experimental scope (datasets, conditions tested)
- Claims about "why" something works vs. evidence provided (ablations, analysis)

Return JSON array of claim-evidence gap issues found."""
    },

    "data_leakage": {
        "name": "Data Leakage",
        "description": "Detects potential data leakage between train/validation/test sets",
        "system_prompt": SYSTEM_PROMPT_TEMPLATE.format(category_name="data leakage"),
        "user_prompt_template": """Analyze this paper for data leakage issues.

Look for:
- Test data used during model training or hyperparameter tuning
- Validation data contaminating training set
- Information from test set influencing model selection or design
- Temporal leakage (future information used to predict past)
- Feature engineering using statistics from entire dataset (including test set)
- Cross-validation issues (data points appearing in both train and test)
- Pre-processing applied to combined data before splitting
- Missing clear description of train/validation/test split procedures

Paper Data:
{paper_data}

Focus especially on:
- How train/validation/test splits are described
- When data preprocessing steps occur (before or after splitting)
- How hyperparameters were selected and on which data
- Whether test set was used for any decisions during development
- For time-series: whether future information leaks into past predictions

This is CRITICAL - data leakage invalidates experimental results.
Return JSON array of data leakage issues found."""
    },

    "unfair_comparison": {
        "name": "Unfair Comparison",
        "description": "Detects unfair or misleading comparisons with baseline methods",
        "system_prompt": SYSTEM_PROMPT_TEMPLATE.format(category_name="unfair comparison"),
        "user_prompt_template": """Analyze this paper for unfair comparison issues.

Look for:
- Comparing against outdated or weak baselines
- Different experimental conditions for proposed method vs. baselines
- Baselines not properly tuned or optimized
- Proposed method using more data, compute, or iterations than baselines
- Cherry-picking metrics that favor the proposed method
- Missing comparisons with recent state-of-the-art methods
- Different evaluation protocols for different methods
- Unfair advantages in implementation (e.g., more recent libraries, hardware)
- Baselines implemented poorly or not using best practices

Paper Data:
{paper_data}

Focus especially on:
- Years of baseline methods vs. current state-of-the-art
- Whether baselines were re-implemented or used from papers
- Hyperparameter tuning for baselines vs. proposed method
- Computational resources allocated to each method
- Whether all methods evaluated on same data under same conditions
- Metrics selection and whether it favors proposed approach

This is CRITICAL - unfair comparisons mislead readers about true contributions.
Return JSON array of unfair comparison issues found."""
    },

    "cherry_picking": {
        "name": "Cherry Picking",
        "description": "Detects selective reporting of favorable results while hiding unfavorable ones",
        "system_prompt": SYSTEM_PROMPT_TEMPLATE.format(category_name="cherry picking"),
        "user_prompt_template": """Analyze this paper for cherry picking issues.

Look for:
- Selective reporting of datasets where method works well
- Missing results on standard benchmarks where method likely performs poorly
- Reporting only favorable metrics while omitting standard metrics
- Showing only best runs or cherry-picked examples
- Incomplete ablation studies that hide negative results
- Selective reporting of experimental conditions
- Missing error bars or variance information to hide inconsistency
- Focusing on outlier cases rather than average performance
- Reporting results only for specific hyperparameter settings

Paper Data:
{paper_data}

Focus especially on:
- Whether standard benchmarks in the field are missing
- Whether reported metrics are unusual or non-standard
- Whether only a subset of experimental conditions are shown
- Whether statistical measures (std, variance, error bars) are missing
- Whether ablation studies are comprehensive or selective
- Whether negative results or failure cases are discussed

Return JSON array of cherry picking issues found."""
    },

    "missing_ablation": {
        "name": "Missing Ablation",
        "description": "Detects insufficient ablation studies to validate design choices",
        "system_prompt": SYSTEM_PROMPT_TEMPLATE.format(category_name="missing ablation"),
        "user_prompt_template": """Analyze this paper for missing ablation study issues.

Look for:
- Novel components introduced without ablation to show their impact
- Multiple design choices made without justification through ablations
- Claimed contributions not validated by removing them
- Missing component-wise analysis of proposed method
- Lack of sensitivity analysis for hyperparameters
- Missing comparison of design alternatives
- No analysis of which parts of the method contribute to performance
- Complex methods without breakdown of component contributions

Paper Data:
{paper_data}

Focus especially on:
- Main technical contributions and whether they're ablated
- Novel architectural components or algorithmic choices
- Whether each claimed contribution is validated by removing it
- Whether design alternatives were explored
- Whether ablation results show meaningful improvements
- For multi-component methods: whether each component is ablated

Good ablation studies show:
- Performance with full method vs. removing each component
- Statistical significance of each component's contribution
- Analysis of why each component helps

Return JSON array of missing ablation issues found."""
    },

    "statistical_validity": {
        "name": "Statistical Validity",
        "description": "Detects statistical issues like missing significance tests, small sample sizes, or invalid conclusions",
        "system_prompt": SYSTEM_PROMPT_TEMPLATE.format(category_name="statistical validity"),
        "user_prompt_template": """Analyze this paper for statistical validity issues.

Look for:
- Claims of improvement without significance tests
- Missing error bars, standard deviations, or confidence intervals
- Small sample sizes without acknowledging limitations
- Multiple comparisons without correction (p-hacking risk)
- Invalid statistical tests for the data type
- Confusing correlation with causation
- Cherry-picking significance level after seeing results
- Missing information about number of runs or trials
- Comparing means without considering variance
- Claims based on single runs without replication

Paper Data:
{paper_data}

Focus especially on:
- Whether improvements over baselines are statistically significant
- Whether error bars or confidence intervals are reported
- Sample sizes for experiments (number of runs, test examples)
- Whether appropriate statistical tests are used
- Whether multiple testing correction is applied when needed
- Whether assumptions of statistical tests are met
- Whether negative results are explained or just ignored

Statistical rigor indicators:
- Reporting mean ± std over multiple runs
- Significance tests (t-test, Wilcoxon, etc.)
- Confidence intervals
- Effect sizes beyond just p-values
- Acknowledgment of statistical limitations

Return JSON array of statistical validity issues found."""
    },

    "implicit_assumption": {
        "name": "Implicit Assumption",
        "description": "Detects unstated assumptions that may not hold in practice",
        "system_prompt": SYSTEM_PROMPT_TEMPLATE.format(category_name="implicit assumption"),
        "user_prompt_template": """Analyze this paper for implicit assumption issues.

Look for:
- Unstated assumptions about data distribution
- Assumptions about problem structure not validated
- Implicit assumptions about deployment conditions
- Assumptions about user behavior or requirements
- Unstated computational or resource assumptions
- Assumptions about generalization not tested
- Implicit assumptions in problem formulation
- Assumptions about access to certain information
- Idealized conditions assumed without discussion

Paper Data:
{paper_data}

Focus especially on:
- What conditions must hold for the method to work as claimed
- Assumptions about data quality, distribution, or availability
- Assumptions about computational resources or latency requirements
- Assumptions about how method will be used in practice
- Gap between experimental setup and real-world deployment
- Whether method assumes access to information not available in practice
- Whether simplifying assumptions are stated and justified

Common implicit assumptions to watch for:
- IID (independent, identically distributed) data
- Stationarity of data distribution
- Availability of labeled data
- Perfect labels without noise
- Computational resources are unlimited
- Real-time processing not required
- Single-domain application

Return JSON array of implicit assumption issues found."""
    },

    "reproducibility": {
        "name": "Reproducibility",
        "description": "Detects missing information needed to reproduce the work",
        "system_prompt": SYSTEM_PROMPT_TEMPLATE.format(category_name="reproducibility"),
        "user_prompt_template": """Analyze this paper for reproducibility issues.

Look for:
- Missing implementation details
- Hyperparameters not specified
- Random seeds not mentioned
- Dataset details incomplete
- Training procedures not fully described
- Computational requirements not stated
- Code availability not mentioned
- Missing architectural details
- Evaluation protocol not fully specified
- Dependencies and library versions not listed

Paper Data:
{paper_data}

Focus especially on:
- Are hyperparameters fully specified?
- Is the model architecture completely described?
- Is the training procedure detailed enough to replicate?
- Are dataset versions and splits clearly defined?
- Is code/data publicly available or promised?
- Are hardware requirements and training time mentioned?
- Can someone reproduce the main results from the paper alone?

Reproducibility checklist:
- Model architecture: layers, sizes, activation functions
- Training: optimizer, learning rate, batch size, epochs, early stopping
- Data: exact datasets, versions, preprocessing, splits
- Evaluation: metrics, protocols, statistical testing
- Implementation: frameworks, libraries, hardware
- Code/data sharing: GitHub links, data availability

Missing any of these reduces reproducibility.
Return JSON array of reproducibility issues found."""
    },

    "causal_overclaim": {
        "name": "Causal Overclaim",
        "description": "Detects causal claims not supported by experimental design",
        "system_prompt": SYSTEM_PROMPT_TEMPLATE.format(category_name="causal overclaim"),
        "user_prompt_template": """Analyze this paper for causal overclaim issues.

Look for:
- Causal language (causes, leads to, because, due to) without causal evidence
- Correlation presented as causation
- Claims about mechanisms without proper validation
- Explanations of "why" without controlled experiments
- Claims that X causes Y based only on observational data
- Causal interpretations of neural network components without proper analysis
- Claiming feature importance implies causality
- Missing confounding variable consideration
- Reverse causality not ruled out

Paper Data:
{paper_data}

Focus especially on:
- Use of causal language: "causes", "improves performance because", "X leads to Y"
- Whether causal claims are backed by controlled experiments
- Whether ablation studies support causal interpretations
- Whether observational correlations are misrepresented as causal
- Whether confounding variables are considered and controlled
- Whether proposed mechanisms are actually validated

Causal claims require:
- Controlled experiments (not just correlations)
- Ablation studies showing X → Y relationship
- Ruling out confounding factors
- Temporal ordering (cause before effect)
- Mechanistic validation (not just correlation)

Acceptable causal evidence:
- Randomized controlled experiments
- Comprehensive ablations showing X causes Y
- Intervention studies
- Theoretical analysis with empirical validation

Not acceptable:
- Correlation analysis alone
- Post-hoc explanations without validation
- Observational data without controls

Return JSON array of causal overclaim issues found."""
    }
}


def get_category_prompt(category: str) -> dict[str, str]:
    """Get the prompt configuration for a specific category.

    Args:
        category: One of the 9 supported category names

    Returns:
        Dictionary with 'name', 'description', 'system_prompt', and 'user_prompt_template'

    Raises:
        ValueError: If category is not recognized
    """
    if category not in CATEGORY_PROMPTS:
        valid_categories = ", ".join(sorted(CATEGORY_PROMPTS.keys()))
        raise ValueError(
            f"Unknown category '{category}'. Valid categories are: {valid_categories}"
        )
    return CATEGORY_PROMPTS[category]


def format_user_prompt(category: str, paper_data: str) -> str:
    """Format the user prompt for a category with paper data.

    Args:
        category: One of the 9 supported category names
        paper_data: JSON string or formatted text representation of paper data

    Returns:
        Formatted user prompt ready to send to Claude API

    Raises:
        ValueError: If category is not recognized
    """
    prompt_config = get_category_prompt(category)
    return prompt_config["user_prompt_template"].format(paper_data=paper_data)


def get_all_categories() -> list[str]:
    """Get list of all supported category names.

    Returns:
        List of 9 category names
    """
    return sorted(CATEGORY_PROMPTS.keys())


# Validate that we have exactly 9 categories
assert len(CATEGORY_PROMPTS) == 9, f"Expected 9 categories, found {len(CATEGORY_PROMPTS)}"
