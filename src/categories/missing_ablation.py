"""Missing ablation category checker.

Detects insufficient ablation studies that fail to demonstrate which
components of a proposed method contribute to its performance.
"""

import json
from typing import Optional

from src.categories.base import BaseChecker
from src.claude_client import ClaudeClientError
from src.models.issue import Evidence, MethodologicalIssue, Severity
from src.models.paper_data import PaperData
from src.prompts import get_category_prompt, format_user_prompt


class MissingAblationChecker(BaseChecker):
    """Checker for missing ablation issues.

    Ablation studies systematically remove or modify components of a method
    to understand their individual contributions. Missing or insufficient
    ablation studies make it impossible to determine which components are
    necessary and which contribute most to performance.

    Common types of missing ablation:
    - No ablation studies for multi-component methods
    - Incomplete ablation (not testing all components)
    - Ablation only on a single dataset or metric
    - Missing analysis of component interactions
    - No justification for design choices
    - Insufficient comparison with simpler baselines
    - Missing sensitivity analysis for hyperparameters
    - Lack of component-wise contribution quantification

    Example:
        >>> checker = MissingAblationChecker(claude_client)
        >>> issues = checker.check(paper_data)
        >>> for issue in issues:
        ...     print(f"{issue.severity}: {issue.title}")
    """

    def __init__(self, claude_client):
        """Initialize missing ablation checker.

        Args:
            claude_client: ClaudeClient instance for API calls
        """
        super().__init__(claude_client, category="missing_ablation")

    def check(self, paper_data: PaperData) -> list[MethodologicalIssue]:
        """Check paper data for missing ablation issues.

        Args:
            paper_data: Structured paper data from Stage 1 extraction

        Returns:
            List of MethodologicalIssue objects for missing ablation issues found.
            Returns empty list if no issues found.

        Raises:
            ClaudeClientError: If API call fails and fallback is not available
            ValueError: If paper_data is invalid or missing required fields
        """
        if not paper_data:
            raise ValueError("paper_data cannot be None")

        # Format paper data for the prompt
        formatted_data = self._format_paper_data(paper_data)

        # Get category-specific prompts
        prompt_config = get_category_prompt(self.category)
        system_prompt = prompt_config["system_prompt"]
        user_prompt = format_user_prompt(self.category, formatted_data)

        # Call Claude API
        try:
            response = self.claude_client.generate(
                prompt=user_prompt,
                system_prompt=system_prompt,
                max_tokens=4096,
                temperature=0.3,  # Lower temperature for more consistent analysis
            )

            # Parse JSON response
            issues_data = self._parse_response(response.content)

            # Convert to MethodologicalIssue objects
            issues = []
            for issue_dict in issues_data:
                issue = self._dict_to_issue(issue_dict)
                if issue:
                    issues.append(issue)

            return issues

        except ClaudeClientError as e:
            # Re-raise with more context
            raise ClaudeClientError(
                f"Failed to check missing ablation: {str(e)}"
            ) from e
        except Exception as e:
            raise ValueError(
                f"Failed to parse missing ablation check results: {str(e)}"
            ) from e

    def _parse_response(self, content: str) -> list[dict]:
        """Parse Claude's JSON response into a list of issue dictionaries.

        Args:
            content: Raw response content from Claude API

        Returns:
            List of dictionaries containing issue data

        Raises:
            ValueError: If response is not valid JSON or has unexpected format
        """
        # Try to find JSON array in the response
        content = content.strip()

        # Handle case where response is wrapped in markdown code blocks
        if content.startswith("```"):
            # Extract JSON from code block
            lines = content.split("\n")
            json_lines = []
            in_code_block = False
            for line in lines:
                if line.startswith("```"):
                    in_code_block = not in_code_block
                    continue
                if in_code_block:
                    json_lines.append(line)
            content = "\n".join(json_lines).strip()

        # Parse JSON
        try:
            issues_data = json.loads(content)
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON response: {str(e)}")

        # Validate it's a list
        if not isinstance(issues_data, list):
            raise ValueError(f"Expected JSON array, got {type(issues_data)}")

        return issues_data

    def _dict_to_issue(self, issue_dict: dict) -> Optional[MethodologicalIssue]:
        """Convert an issue dictionary to a MethodologicalIssue object.

        Args:
            issue_dict: Dictionary containing issue data from Claude API

        Returns:
            MethodologicalIssue object, or None if conversion fails
        """
        try:
            # Map severity string to Severity enum
            severity_str = issue_dict.get("severity", "warning").lower()
            severity = Severity(severity_str)

            # Build evidence object
            evidence = Evidence(
                section=issue_dict.get("evidence_section"),
                quote=issue_dict.get("evidence_quote"),
                table_reference=issue_dict.get("evidence_table"),
            )

            # Create MethodologicalIssue
            return MethodologicalIssue(
                category=self.category,
                severity=severity,
                confidence=float(issue_dict.get("confidence", 0.7)),
                title=issue_dict.get("title", "Missing ablation study detected"),
                description=issue_dict.get("description", ""),
                evidence=evidence,
                suggestions=issue_dict.get("suggestions", []),
            )

        except (ValueError, KeyError, TypeError) as e:
            # Log warning and skip this issue
            # In production, would use proper logging
            print(f"Warning: Failed to parse issue: {str(e)}")
            return None
