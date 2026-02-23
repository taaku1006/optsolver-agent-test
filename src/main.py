"""Main entry point and CLI interface for the Logic Checker.

This module provides a command-line interface to run methodological issue
detection on research papers. It accepts paper data (from Stage 1) and outputs
detected issues as JSON.

Example usage:
    python -m src.main paper_data.json
    python -m src.main paper_data.json --output results.json
    python -m src.main paper_data.json --api-key sk-... --model claude-3-opus-20240229
"""

import argparse
import json
import logging
import sys
from pathlib import Path
from typing import Optional

from src.claude_client import ClaudeClient, ClaudeClientError
from src.logic_checker import LogicChecker
from src.models.paper_data import PaperData

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def load_paper_data(file_path: Path) -> PaperData:
    """Load and validate paper data from JSON file.

    Args:
        file_path: Path to JSON file containing paper data

    Returns:
        Validated PaperData object

    Raises:
        FileNotFoundError: If file doesn't exist
        json.JSONDecodeError: If file contains invalid JSON
        ValueError: If data doesn't match PaperData schema
    """
    if not file_path.exists():
        raise FileNotFoundError(f"Paper data file not found: {file_path}")

    logger.info(f"Loading paper data from {file_path}")

    with open(file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    # Validate against PaperData model
    try:
        paper_data = PaperData.model_validate(data)
        logger.info(f"Successfully loaded paper: {paper_data.metadata.title or 'Unknown'}")
        return paper_data
    except Exception as e:
        raise ValueError(f"Invalid paper data format: {str(e)}") from e


def save_results(results: dict, output_path: Optional[Path]) -> None:
    """Save results to file or stdout.

    Args:
        results: Results dictionary to save
        output_path: Optional path to output file. If None, prints to stdout.
    """
    output_json = json.dumps(results, indent=2, ensure_ascii=False)

    if output_path:
        logger.info(f"Saving results to {output_path}")
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(output_json)
        logger.info(f"Results saved successfully")
    else:
        # Print to stdout (without logging prefix)
        print(output_json)


def main() -> int:
    """Main entry point for CLI.

    Returns:
        Exit code (0 for success, non-zero for errors)
    """
    parser = argparse.ArgumentParser(
        description='Logic Checker - Detect methodological issues in research papers',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s paper_data.json
  %(prog)s paper_data.json --output results.json
  %(prog)s paper_data.json --no-parallel --verbose
  %(prog)s paper_data.json --api-key sk-... --model claude-3-opus-20240229

Environment Variables:
  ANTHROPIC_API_KEY    API key for Claude (required if not passed via --api-key)
        """
    )

    # Required arguments
    parser.add_argument(
        'input_file',
        type=Path,
        help='Path to JSON file containing paper data (from Stage 1 extraction)'
    )

    # Optional arguments
    parser.add_argument(
        '-o', '--output',
        type=Path,
        metavar='FILE',
        help='Output file path for results (default: stdout)'
    )

    parser.add_argument(
        '--api-key',
        type=str,
        metavar='KEY',
        help='Anthropic API key (default: ANTHROPIC_API_KEY environment variable)'
    )

    parser.add_argument(
        '--model',
        type=str,
        metavar='MODEL',
        help='Claude model to use (default: claude-3-5-sonnet-20241022)'
    )

    parser.add_argument(
        '--max-workers',
        type=int,
        metavar='N',
        help='Maximum number of parallel workers for category checks (default: auto)'
    )

    parser.add_argument(
        '--no-parallel',
        action='store_true',
        help='Disable parallel execution (useful for debugging)'
    )

    parser.add_argument(
        '--timeout',
        type=float,
        metavar='SECONDS',
        default=60.0,
        help='API request timeout in seconds (default: 60.0)'
    )

    parser.add_argument(
        '--max-retries',
        type=int,
        metavar='N',
        default=3,
        help='Maximum number of retry attempts for failed API requests (default: 3)'
    )

    parser.add_argument(
        '-v', '--verbose',
        action='store_true',
        help='Enable verbose logging'
    )

    parser.add_argument(
        '--version',
        action='version',
        version='%(prog)s 1.0.0 - Stage 2 Logic Checker'
    )

    args = parser.parse_args()

    # Configure logging level
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
        logger.debug("Verbose logging enabled")

    try:
        # Load paper data
        paper_data = load_paper_data(args.input_file)

        # Initialize Claude client
        logger.info("Initializing Claude API client")
        try:
            claude_client = ClaudeClient(
                api_key=args.api_key,
                model=args.model,
                max_retries=args.max_retries,
                timeout=args.timeout,
            )
        except ClaudeClientError as e:
            logger.error(f"Failed to initialize Claude client: {str(e)}")
            return 1

        # Initialize Logic Checker
        logger.info("Initializing Logic Checker")
        logic_checker = LogicChecker(
            claude_client=claude_client,
            max_workers=args.max_workers,
            enable_parallel=not args.no_parallel,
        )

        # Run analysis
        logger.info("Starting methodological issue detection")
        logger.info(f"Parallel execution: {'disabled' if args.no_parallel else 'enabled'}")

        result = logic_checker.check(paper_data)

        # Log summary
        logger.info(f"Analysis complete:")
        logger.info(f"  - Issues found: {len(result.issues)}")
        logger.info(f"  - Categories checked: {result.successful_categories}/{result.total_categories}")
        logger.info(f"  - Success rate: {result.success_rate:.1%}")

        if result.is_partial:
            logger.warning(f"  - Failed categories: {', '.join(result.failed_categories)}")
            logger.warning("  - Results are PARTIAL due to some category failures")

        # Save results
        results_dict = result.to_dict()
        save_results(results_dict, args.output)

        # Return success (even for partial results)
        return 0

    except FileNotFoundError as e:
        logger.error(f"File error: {str(e)}")
        return 1
    except json.JSONDecodeError as e:
        logger.error(f"JSON parsing error: {str(e)}")
        return 1
    except ValueError as e:
        logger.error(f"Validation error: {str(e)}")
        return 1
    except KeyboardInterrupt:
        logger.info("Analysis interrupted by user")
        return 130  # Standard exit code for SIGINT
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}", exc_info=args.verbose)
        return 1


if __name__ == '__main__':
    sys.exit(main())
