"""Claude API client wrapper with error handling and fallback mechanisms."""

import os
import time
from typing import Any, Optional

from anthropic import Anthropic, APIError, APIStatusError, RateLimitError
from pydantic import BaseModel


class ClaudeResponse(BaseModel):
    """Response from Claude API."""

    content: str
    model: str
    usage: dict[str, Any]
    stop_reason: Optional[str] = None


class ClaudeClientError(Exception):
    """Base exception for Claude client errors."""

    pass


class ClaudeClient:
    """Claude API client with error handling and retry logic.

    Features:
    - Automatic retry on rate limits and transient errors
    - Configurable timeouts
    - Fallback mechanisms for partial failures
    - Structured response parsing

    Example:
        >>> client = ClaudeClient(api_key="sk-...")
        >>> response = client.generate(
        ...     prompt="Analyze this paper for data leakage issues",
        ...     max_tokens=1024
        ... )
        >>> print(response.content)
    """

    DEFAULT_MODEL = "claude-3-5-sonnet-20241022"
    DEFAULT_MAX_TOKENS = 4096
    DEFAULT_MAX_RETRIES = 3
    DEFAULT_RETRY_DELAY = 1.0  # seconds
    DEFAULT_TIMEOUT = 60.0  # seconds

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: Optional[str] = None,
        max_retries: int = DEFAULT_MAX_RETRIES,
        retry_delay: float = DEFAULT_RETRY_DELAY,
        timeout: float = DEFAULT_TIMEOUT,
    ):
        """Initialize Claude API client.

        Args:
            api_key: Anthropic API key. If not provided, reads from ANTHROPIC_API_KEY env var.
            model: Claude model to use. Defaults to claude-3-5-sonnet-20241022.
            max_retries: Maximum number of retry attempts for failed requests.
            retry_delay: Initial delay between retries in seconds (exponential backoff applied).
            timeout: Request timeout in seconds.

        Raises:
            ClaudeClientError: If API key is not provided and not found in environment.
        """
        self.api_key = api_key or os.getenv("ANTHROPIC_API_KEY")
        if not self.api_key:
            raise ClaudeClientError(
                "API key not provided. Set ANTHROPIC_API_KEY environment variable "
                "or pass api_key to ClaudeClient constructor."
            )

        self.model = model or self.DEFAULT_MODEL
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.timeout = timeout

        self.client = Anthropic(api_key=self.api_key, timeout=self.timeout)

    def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        max_tokens: Optional[int] = None,
        temperature: float = 1.0,
        model: Optional[str] = None,
    ) -> ClaudeResponse:
        """Generate a response from Claude API.

        Args:
            prompt: The user prompt to send to Claude.
            system_prompt: Optional system prompt for instruction/context.
            max_tokens: Maximum tokens in response. Defaults to DEFAULT_MAX_TOKENS.
            temperature: Sampling temperature (0-1). Higher = more random.
            model: Claude model to use. Defaults to instance model.

        Returns:
            ClaudeResponse with content, model, usage, and stop_reason.

        Raises:
            ClaudeClientError: If request fails after all retries.
        """
        max_tokens = max_tokens or self.DEFAULT_MAX_TOKENS
        model = model or self.model

        messages = [{"role": "user", "content": prompt}]

        kwargs: dict[str, Any] = {
            "model": model,
            "max_tokens": max_tokens,
            "messages": messages,
            "temperature": temperature,
        }

        if system_prompt:
            kwargs["system"] = system_prompt

        return self._call_with_retry(**kwargs)

    def _call_with_retry(self, **kwargs: Any) -> ClaudeResponse:
        """Call Claude API with retry logic.

        Args:
            **kwargs: Arguments to pass to the Anthropic messages.create() API.

        Returns:
            ClaudeResponse with parsed response data.

        Raises:
            ClaudeClientError: If request fails after all retries.
        """
        last_error: Optional[Exception] = None

        for attempt in range(self.max_retries):
            try:
                response = self.client.messages.create(**kwargs)

                # Extract text content from response
                content = ""
                if response.content:
                    # Handle both single and multiple content blocks
                    for block in response.content:
                        if hasattr(block, "text"):
                            content += block.text

                return ClaudeResponse(
                    content=content,
                    model=response.model,
                    usage={
                        "input_tokens": response.usage.input_tokens,
                        "output_tokens": response.usage.output_tokens,
                    },
                    stop_reason=response.stop_reason,
                )

            except RateLimitError as e:
                last_error = e
                # Rate limit error - wait longer before retry
                delay = self.retry_delay * (2**attempt) * 2
                if attempt < self.max_retries - 1:
                    time.sleep(delay)
                continue

            except APIStatusError as e:
                last_error = e
                # Retry on server errors (5xx) but not client errors (4xx)
                if e.status_code >= 500 and attempt < self.max_retries - 1:
                    delay = self.retry_delay * (2**attempt)
                    time.sleep(delay)
                    continue
                else:
                    # Don't retry on client errors
                    raise ClaudeClientError(
                        f"API request failed with status {e.status_code}: {e.message}"
                    ) from e

            except APIError as e:
                last_error = e
                # Generic API error - retry with exponential backoff
                if attempt < self.max_retries - 1:
                    delay = self.retry_delay * (2**attempt)
                    time.sleep(delay)
                    continue
                else:
                    raise ClaudeClientError(f"API request failed: {str(e)}") from e

            except Exception as e:
                last_error = e
                # Unexpected error - don't retry
                raise ClaudeClientError(f"Unexpected error: {str(e)}") from e

        # All retries exhausted
        raise ClaudeClientError(
            f"Request failed after {self.max_retries} retries. Last error: {str(last_error)}"
        ) from last_error

    def generate_with_fallback(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        max_tokens: Optional[int] = None,
        temperature: float = 1.0,
        model: Optional[str] = None,
        fallback_response: Optional[str] = None,
    ) -> tuple[Optional[ClaudeResponse], Optional[str]]:
        """Generate a response with fallback on failure.

        This method is designed for scenarios where partial failures are acceptable,
        such as running multiple category checks in parallel. If the API call fails,
        it returns a fallback response instead of raising an exception.

        Args:
            prompt: The user prompt to send to Claude.
            system_prompt: Optional system prompt for instruction/context.
            max_tokens: Maximum tokens in response. Defaults to DEFAULT_MAX_TOKENS.
            temperature: Sampling temperature (0-1). Higher = more random.
            model: Claude model to use. Defaults to instance model.
            fallback_response: Optional fallback response to return on failure.

        Returns:
            Tuple of (response, error):
            - response: ClaudeResponse if successful, None if failed
            - error: Error message string if failed, None if successful
        """
        try:
            response = self.generate(
                prompt=prompt,
                system_prompt=system_prompt,
                max_tokens=max_tokens,
                temperature=temperature,
                model=model,
            )
            return response, None

        except ClaudeClientError as e:
            error_msg = str(e)
            if fallback_response:
                # Create a fallback response object
                fallback = ClaudeResponse(
                    content=fallback_response,
                    model=model or self.model,
                    usage={"input_tokens": 0, "output_tokens": 0},
                    stop_reason="error_fallback",
                )
                return fallback, error_msg
            else:
                return None, error_msg

    def batch_generate(
        self,
        prompts: list[tuple[str, Optional[str]]],
        max_tokens: Optional[int] = None,
        temperature: float = 1.0,
        model: Optional[str] = None,
        fail_fast: bool = False,
    ) -> list[tuple[Optional[ClaudeResponse], Optional[str]]]:
        """Generate responses for multiple prompts.

        Args:
            prompts: List of (prompt, system_prompt) tuples.
            max_tokens: Maximum tokens in each response.
            temperature: Sampling temperature (0-1).
            model: Claude model to use.
            fail_fast: If True, stop on first error. If False, continue with fallbacks.

        Returns:
            List of (response, error) tuples for each prompt.
        """
        results: list[tuple[Optional[ClaudeResponse], Optional[str]]] = []

        for prompt, system_prompt in prompts:
            response, error = self.generate_with_fallback(
                prompt=prompt,
                system_prompt=system_prompt,
                max_tokens=max_tokens,
                temperature=temperature,
                model=model,
            )

            results.append((response, error))

            if fail_fast and error:
                # Stop processing remaining prompts
                break

        return results

    def __repr__(self) -> str:
        """String representation of the client."""
        return (
            f"ClaudeClient(model={self.model}, "
            f"max_retries={self.max_retries}, "
            f"timeout={self.timeout})"
        )
