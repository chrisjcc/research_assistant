"""Retry logic and circuit breaker patterns for resilient operations.

This module provides decorators and utilities for handling transient failures
with intelligent retry strategies and circuit breaker patterns.

Example:
    >>> from research_assistant.utils.retry import retry_with_backoff
    >>> @retry_with_backoff(max_retries=3)
    ... def unstable_api_call():
    ...     return call_external_api()
"""

import logging
import time
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from functools import wraps
from typing import Callable, Optional, Tuple, Type, Union

from .exceptions import (
    LLMAPIError,
    LLMTimeoutError,
    RateLimitError,
    SearchTimeoutError,
    WebSearchError,
)

logger = logging.getLogger(__name__)


class CircuitState(str, Enum):
    """Circuit breaker states."""

    CLOSED = "closed"  # Normal operation
    OPEN = "open"  # Failing, rejecting requests
    HALF_OPEN = "half_open"  # Testing if service recovered


@dataclass
class RetryConfig:
    """Configuration for retry behavior."""

    max_retries: int = 3
    initial_delay: float = 1.0
    max_delay: float = 60.0
    backoff_factor: float = 2.0
    jitter: bool = True
    exponential: bool = True

    def get_delay(self, attempt: int) -> float:
        """Calculate delay for given attempt.

        Args:
            attempt: Current attempt number (0-indexed).

        Returns:
            Delay in seconds.
        """
        if self.exponential:
            delay = min(self.initial_delay * (self.backoff_factor**attempt), self.max_delay)
        else:
            delay = self.initial_delay

        # Add jitter to prevent thundering herd
        if self.jitter:
            import random

            delay = delay * (0.5 + random.random() * 0.5)

        return delay


@dataclass
class CircuitBreakerConfig:
    """Configuration for circuit breaker."""

    failure_threshold: int = 5  # Failures before opening
    success_threshold: int = 2  # Successes to close from half-open
    timeout: float = 60.0  # Seconds before attempting half-open

    # Tracking
    _failure_count: int = field(default=0, init=False)
    _success_count: int = field(default=0, init=False)
    _last_failure_time: Optional[datetime] = field(default=None, init=False)
    _state: CircuitState = field(default=CircuitState.CLOSED, init=False)

    def record_success(self) -> None:
        """Record a successful operation."""
        self._failure_count = 0

        if self._state == CircuitState.HALF_OPEN:
            self._success_count += 1
            if self._success_count >= self.success_threshold:
                self._state = CircuitState.CLOSED
                self._success_count = 0
                logger.info("Circuit breaker closed after recovery")

    def record_failure(self) -> None:
        """Record a failed operation."""
        self._failure_count += 1
        self._last_failure_time = datetime.now()

        if self._state == CircuitState.HALF_OPEN:
            self._state = CircuitState.OPEN
            self._success_count = 0
            logger.warning("Circuit breaker opened again after test failure")

        elif self._failure_count >= self.failure_threshold:
            self._state = CircuitState.OPEN
            logger.error(f"Circuit breaker opened after {self._failure_count} failures")

    def can_attempt(self) -> bool:
        """Check if operation can be attempted.

        Returns:
            True if operation should proceed, False if circuit is open.
        """
        if self._state == CircuitState.CLOSED:
            return True

        if self._state == CircuitState.OPEN:
            # Check if timeout has passed
            if self._last_failure_time:
                elapsed = (datetime.now() - self._last_failure_time).total_seconds()
                if elapsed >= self.timeout:
                    self._state = CircuitState.HALF_OPEN
                    self._success_count = 0
                    logger.info("Circuit breaker entering half-open state")
                    return True
            return False

        # HALF_OPEN state - allow attempt
        return True

    @property
    def state(self) -> CircuitState:
        """Get current circuit state."""
        return self._state


# Global circuit breakers for different services
_CIRCUIT_BREAKERS: dict[str, CircuitBreakerConfig] = {}


def get_circuit_breaker(
    service: str, config: Optional[CircuitBreakerConfig] = None
) -> CircuitBreakerConfig:
    """Get or create circuit breaker for a service.

    Args:
        service: Service identifier.
        config: Optional custom configuration.

    Returns:
        CircuitBreakerConfig instance.
    """
    if service not in _CIRCUIT_BREAKERS:
        _CIRCUIT_BREAKERS[service] = config or CircuitBreakerConfig()
    return _CIRCUIT_BREAKERS[service]


def retry_with_backoff(
    max_retries: int = 3,
    initial_delay: float = 1.0,
    max_delay: float = 60.0,
    backoff_factor: float = 2.0,
    exceptions: Union[Type[Exception], Tuple[Type[Exception], ...]] = Exception,
    on_retry: Optional[Callable[[Exception, int], None]] = None,
    jitter: bool = True,
):
    """Decorator for retrying functions with exponential backoff.

    Args:
        max_retries: Maximum number of retry attempts.
        initial_delay: Initial delay between retries in seconds.
        max_delay: Maximum delay between retries in seconds.
        backoff_factor: Multiplier for delay after each retry.
        exceptions: Exception types to catch and retry on.
        on_retry: Optional callback function called on each retry.
        jitter: Whether to add random jitter to delays.

    Example:
        >>> @retry_with_backoff(max_retries=3, initial_delay=1.0)
        ... def api_call():
        ...     return requests.get("https://api.example.com")
    """
    config = RetryConfig(
        max_retries=max_retries,
        initial_delay=initial_delay,
        max_delay=max_delay,
        backoff_factor=backoff_factor,
        jitter=jitter,
    )

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            last_exception = None

            for attempt in range(max_retries + 1):
                try:
                    result = func(*args, **kwargs)

                    if attempt > 0:
                        logger.info(f"{func.__name__} succeeded after {attempt} retries")

                    return result

                except exceptions as e:
                    last_exception = e

                    if attempt == max_retries:
                        logger.error(
                            f"{func.__name__} failed after {max_retries} retries: {str(e)}"
                        )
                        raise

                    delay = config.get_delay(attempt)

                    logger.warning(
                        f"{func.__name__} failed (attempt {attempt + 1}/{max_retries + 1}), "
                        f"retrying in {delay:.2f}s: {str(e)}"
                    )

                    # Call retry callback if provided
                    if on_retry:
                        on_retry(e, attempt)

                    time.sleep(delay)

            # Should never reach here, but just in case
            raise last_exception

        return wrapper

    return decorator


def retry_on_rate_limit(max_retries: int = 5, initial_delay: float = 2.0, max_delay: float = 120.0):
    """Decorator specifically for handling rate limit errors.

    Uses longer delays and more retries than standard retry.

    Args:
        max_retries: Maximum retry attempts.
        initial_delay: Initial delay (should be longer for rate limits).
        max_delay: Maximum delay.

    Example:
        >>> @retry_on_rate_limit(max_retries=5)
        ... def api_call_with_quota():
        ...     return expensive_api_call()
    """

    def on_rate_limit_retry(exception: Exception, attempt: int):
        if isinstance(exception, RateLimitError):
            retry_after = exception.details.get("retry_after_seconds")
            if retry_after:
                logger.info(f"Rate limit retry_after: {retry_after}s")

    return retry_with_backoff(
        max_retries=max_retries,
        initial_delay=initial_delay,
        max_delay=max_delay,
        backoff_factor=2.5,  # Slower backoff for rate limits
        exceptions=(RateLimitError,),
        on_retry=on_rate_limit_retry,
        jitter=True,
    )


def with_circuit_breaker(
    service: str, failure_threshold: int = 5, success_threshold: int = 2, timeout: float = 60.0
):
    """Decorator to add circuit breaker protection to a function.

    Args:
        service: Service identifier for the circuit breaker.
        failure_threshold: Failures before opening circuit.
        success_threshold: Successes needed to close from half-open.
        timeout: Seconds before attempting half-open.

    Example:
        >>> @with_circuit_breaker("external_api")
        ... def call_external_api():
        ...     return api.get_data()
    """
    config = CircuitBreakerConfig(
        failure_threshold=failure_threshold, success_threshold=success_threshold, timeout=timeout
    )
    circuit = get_circuit_breaker(service, config)

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            if not circuit.can_attempt():
                raise Exception(
                    f"Circuit breaker is OPEN for {service}. "
                    f"Wait {circuit.timeout}s before retry."
                )

            try:
                result = func(*args, **kwargs)
                circuit.record_success()
                return result

            except Exception as e:
                circuit.record_failure()
                raise

        return wrapper

    return decorator


def with_timeout(seconds: float):
    """Decorator to add timeout to function execution.

    Args:
        seconds: Timeout in seconds.

    Example:
        >>> @with_timeout(30.0)
        ... def slow_operation():
        ...     return process_data()
    """
    import signal

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            def timeout_handler(signum, frame):
                raise TimeoutError(f"{func.__name__} timed out after {seconds}s")

            # Set the signal handler
            old_handler = signal.signal(signal.SIGALRM, timeout_handler)
            signal.setitimer(signal.ITIMER_REAL, seconds)

            try:
                result = func(*args, **kwargs)
            finally:
                signal.setitimer(signal.ITIMER_REAL, 0)
                signal.signal(signal.SIGALRM, old_handler)

            return result

        return wrapper

    return decorator


# Specialized retry decorators for common patterns


def retry_llm_call(max_retries: int = 3):
    """Retry decorator specifically for LLM API calls.

    Handles common LLM errors like timeouts and rate limits.

    Args:
        max_retries: Maximum retry attempts.

    Example:
        >>> @retry_llm_call(max_retries=3)
        ... def generate_text(prompt):
        ...     return llm.invoke(prompt)
    """
    return retry_with_backoff(
        max_retries=max_retries,
        initial_delay=1.0,
        backoff_factor=2.0,
        exceptions=(LLMAPIError, LLMTimeoutError, RateLimitError),
        jitter=True,
    )


def retry_search_call(max_retries: int = 3):
    """Retry decorator specifically for search operations.

    Handles search-specific errors.

    Args:
        max_retries: Maximum retry attempts.

    Example:
        >>> @retry_search_call(max_retries=3)
        ... def search_web(query):
        ...     return search_api.query(query)
    """
    return retry_with_backoff(
        max_retries=max_retries,
        initial_delay=0.5,
        backoff_factor=2.0,
        exceptions=(WebSearchError, SearchTimeoutError, RateLimitError),
        jitter=True,
    )


# Graceful degradation utilities


class FallbackHandler:
    """Handler for graceful degradation with fallback strategies.

    Example:
        >>> handler = FallbackHandler()
        >>> handler.add_strategy(primary_function)
        >>> handler.add_strategy(fallback_function)
        >>> result = handler.execute(*args)
    """

    def __init__(self):
        """Initialize fallback handler."""
        self.strategies: list[Callable] = []
        self.logger = logging.getLogger(__name__)

    def add_strategy(self, func: Callable) -> None:
        """Add a fallback strategy.

        Args:
            func: Function to try as fallback.
        """
        self.strategies.append(func)

    def execute(self, *args, **kwargs):
        """Execute with fallback strategies.

        Tries each strategy in order until one succeeds.

        Args:
            *args: Positional arguments for strategies.
            **kwargs: Keyword arguments for strategies.

        Returns:
            Result from first successful strategy.

        Raises:
            Exception: If all strategies fail.
        """
        errors = []

        for i, strategy in enumerate(self.strategies):
            try:
                self.logger.debug(f"Trying strategy {i + 1}/{len(self.strategies)}")
                result = strategy(*args, **kwargs)

                if i > 0:
                    self.logger.info(f"Succeeded with fallback strategy {i + 1}")

                return result

            except Exception as e:
                self.logger.warning(f"Strategy {i + 1} failed: {str(e)}")
                errors.append(e)

        # All strategies failed
        self.logger.error(f"All {len(self.strategies)} strategies failed")
        raise Exception(f"All fallback strategies failed. Errors: {[str(e) for e in errors]}")


def with_fallback(*fallback_funcs: Callable):
    """Decorator to add fallback functions.

    Args:
        *fallback_funcs: Functions to try if primary fails.

    Example:
        >>> def fallback_search(query):
        ...     return cached_results(query)
        >>>
        >>> @with_fallback(fallback_search)
        ... def primary_search(query):
        ...     return api_search(query)
    """

    def decorator(primary_func: Callable) -> Callable:
        @wraps(primary_func)
        def wrapper(*args, **kwargs):
            handler = FallbackHandler()
            handler.add_strategy(primary_func)

            for fallback in fallback_funcs:
                handler.add_strategy(fallback)

            return handler.execute(*args, **kwargs)

        return wrapper

    return decorator


def safe_execute(func: Callable, *args, default=None, log_errors: bool = True, **kwargs):
    """Safely execute a function with error handling.

    Args:
        func: Function to execute.
        *args: Positional arguments.
        default: Default value to return on error.
        log_errors: Whether to log errors.
        **kwargs: Keyword arguments.

    Returns:
        Function result or default value on error.

    Example:
        >>> result = safe_execute(risky_operation, default=[])
    """
    try:
        return func(*args, **kwargs)
    except Exception as e:
        if log_errors:
            logger.error(f"Error in {func.__name__}: {str(e)}", exc_info=True)
        return default


# Utility functions


def should_retry(exception: Exception) -> bool:
    """Determine if an exception should trigger a retry.

    Args:
        exception: Exception to check.

    Returns:
        True if should retry, False otherwise.
    """
    from .exceptions import is_recoverable_error

    # Check if it's a recoverable custom exception
    if is_recoverable_error(exception):
        return True

    # Check for common transient errors
    transient_errors = (
        ConnectionError,
        TimeoutError,
        RateLimitError,
        SearchTimeoutError,
        LLMTimeoutError,
    )

    return isinstance(exception, transient_errors)


def get_retry_delay(attempt: int, config: Optional[RetryConfig] = None) -> float:
    """Calculate retry delay for an attempt.

    Args:
        attempt: Current attempt number (0-indexed).
        config: Optional retry configuration.

    Returns:
        Delay in seconds.

    Example:
        >>> delay = get_retry_delay(2)
        >>> time.sleep(delay)
    """
    if config is None:
        config = RetryConfig()

    return config.get_delay(attempt)


def reset_circuit_breaker(service: str) -> None:
    """Manually reset a circuit breaker.

    Args:
        service: Service identifier.

    Example:
        >>> reset_circuit_breaker("external_api")
    """
    if service in _CIRCUIT_BREAKERS:
        circuit = _CIRCUIT_BREAKERS[service]
        circuit._state = CircuitState.CLOSED
        circuit._failure_count = 0
        circuit._success_count = 0
        logger.info(f"Circuit breaker for {service} manually reset")


def get_circuit_breaker_status(service: str) -> dict:
    """Get status of a circuit breaker.

    Args:
        service: Service identifier.

    Returns:
        Dictionary with circuit breaker status.

    Example:
        >>> status = get_circuit_breaker_status("external_api")
        >>> print(status['state'])
    """
    if service not in _CIRCUIT_BREAKERS:
        return {"exists": False}

    circuit = _CIRCUIT_BREAKERS[service]
    return {
        "exists": True,
        "state": circuit.state.value,
        "failure_count": circuit._failure_count,
        "success_count": circuit._success_count,
        "last_failure": (
            circuit._last_failure_time.isoformat() if circuit._last_failure_time else None
        ),
    }
