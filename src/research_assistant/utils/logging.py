"""Structured logging system with context tracking and metrics.

This module provides a comprehensive logging system with:
- Structured logging (JSON) support
- Context managers for tracking node execution
- Performance metrics tracking (timing, tokens, API calls)
- Log aggregation and filtering
- Integration with configuration system

Example:
    >>> from research_assistant.utils.logging import setup_logging, get_logger
    >>> setup_logging(level="INFO", structured=True)
    >>> logger = get_logger(__name__)
    >>> logger.info("Research started", extra={"topic": "AI Safety"})
"""

import json
import logging
import logging.config
import sys
import time
from collections.abc import Callable, Generator
from contextlib import contextmanager
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from functools import wraps
from pathlib import Path
from typing import Any

try:
    import structlog

    STRUCTLOG_AVAILABLE = True
except ImportError:
    STRUCTLOG_AVAILABLE = False


# Global metrics storage
_METRICS_STORE: dict[str, Any] = {
    "api_calls": 0,
    "total_tokens": 0,
    "node_executions": {},
    "errors": [],
    "start_time": None,
}


@dataclass
class ExecutionMetrics:
    """Metrics for tracking execution performance."""

    node_name: str
    start_time: float = field(default_factory=time.time)
    end_time: float | None = None
    duration: float | None = None
    success: bool = True
    error: str | None = None
    tokens_used: int = 0
    api_calls: int = 0
    metadata: dict[str, Any] = field(default_factory=dict)

    def complete(self, success: bool = True, error: str | None = None) -> None:
        """Mark execution as complete.

        Args:
            success: Whether execution succeeded.
            error: Error message if failed.
        """
        self.end_time = time.time()
        self.duration = self.end_time - self.start_time
        self.success = success
        self.error = error

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary.

        Returns:
            Dictionary representation of metrics.
        """
        return asdict(self)


class StructuredFormatter(logging.Formatter):
    """JSON formatter for structured logging."""

    def format(self, record: logging.LogRecord) -> str:
        """Format log record as JSON.

        Args:
            record: Log record to format.

        Returns:
            JSON-formatted log string.
        """
        log_data = {
            "timestamp": datetime.now(timezone.utc).isoformat(),  # noqa: UP017
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }

        # Add exception info if present
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)

        # Add extra fields from record.__dict__
        for key, value in record.__dict__.items():
            if key not in [
                "name",
                "msg",
                "args",
                "created",
                "filename",
                "funcName",
                "levelname",
                "levelno",
                "lineno",
                "module",
                "msecs",
                "message",
                "pathname",
                "process",
                "processName",
                "relativeCreated",
                "thread",
                "threadName",
                "exc_info",
                "exc_text",
                "stack_info",
            ]:
                log_data[key] = value

        return json.dumps(log_data)


class ColoredFormatter(logging.Formatter):
    """Colored console formatter for better readability."""

    # ANSI color codes
    COLORS = {
        "DEBUG": "\033[36m",  # Cyan
        "INFO": "\033[32m",  # Green
        "WARNING": "\033[33m",  # Yellow
        "ERROR": "\033[31m",  # Red
        "CRITICAL": "\033[35m",  # Magenta
        "RESET": "\033[0m",  # Reset
    }

    def format(self, record: logging.LogRecord) -> str:
        """Format log record with colors.

        Args:
            record: Log record to format.

        Returns:
            Colored log string.
        """
        color = self.COLORS.get(record.levelname, self.COLORS["RESET"])
        reset = self.COLORS["RESET"]

        # Color the level name
        record.levelname = f"{color}{record.levelname}{reset}"

        return super().format(record)


def setup_logging(
    level: str = "INFO",
    structured: bool = False,
    log_file: str | None = None,
    console: bool = True,
    colored: bool = True,
    module_levels: dict[str, str] | None = None,
) -> None:
    """Setup logging configuration.

    Args:
        level: Default log level (DEBUG, INFO, WARNING, ERROR, CRITICAL).
        structured: Whether to use JSON structured logging.
        log_file: Optional path to log file.
        console: Whether to log to console.
        colored: Whether to use colored output (console only).
        module_levels: Optional dict of module-specific log levels.

    Example:
        >>> setup_logging(
        ...     level="INFO",
        ...     structured=True,
        ...     log_file="./logs/app.log"
        ... )
    """
    # Create root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, level.upper()))

    # Clear existing handlers
    root_logger.handlers.clear()

    # Create formatters
    formatter: logging.Formatter
    if structured:
        formatter = StructuredFormatter()
    elif colored and console:
        formatter = ColoredFormatter(
            fmt="%(asctime)s - %(name)s - %(levelname)s - %(message)s", datefmt="%Y-%m-%d %H:%M:%S"
        )
    else:
        formatter = logging.Formatter(
            fmt="%(asctime)s - %(name)s - %(levelname)s - %(message)s", datefmt="%Y-%m-%d %H:%M:%S"
        )

    # Console handler
    if console:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(formatter)
        root_logger.addHandler(console_handler)

    # File handler
    if log_file:
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)

        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(StructuredFormatter() if structured else formatter)
        root_logger.addHandler(file_handler)

    # Set module-specific levels
    if module_levels:
        for module, module_level in module_levels.items():
            logging.getLogger(module).setLevel(getattr(logging, module_level.upper()))

    # Reduce noise from common libraries
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)
    logging.getLogger("openai").setLevel(logging.WARNING)
    logging.getLogger("langchain").setLevel(logging.WARNING)

    # Initialize metrics
    _METRICS_STORE["start_time"] = time.time()

    root_logger.info(
        "Logging configured", extra={"level": level, "structured": structured, "log_file": log_file}
    )


def setup_structlog() -> None:
    """Setup structlog if available.

    Provides more advanced structured logging capabilities.

    Example:
        >>> setup_structlog()
        >>> logger = structlog.get_logger()
        >>> logger.info("event", key="value")
    """
    if not STRUCTLOG_AVAILABLE:
        logging.warning("structlog not available, falling back to standard logging")
        return

    structlog.configure(
        processors=[
            structlog.stdlib.filter_by_level,
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            structlog.stdlib.PositionalArgumentsFormatter(),
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.UnicodeDecoder(),
            structlog.processors.JSONRenderer(),
        ],
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )


def get_logger(name: str) -> logging.Logger:
    """Get a logger instance.

    Args:
        name: Logger name (typically __name__).

    Returns:
        Logger instance.

    Example:
        >>> logger = get_logger(__name__)
        >>> logger.info("Message", extra={"key": "value"})
    """
    return logging.getLogger(name)


# Context managers for tracking execution


@contextmanager
def log_execution(
    logger: logging.Logger, node_name: str, level: int = logging.INFO, include_metrics: bool = True
) -> Generator[ExecutionMetrics, None, None]:
    """Context manager for logging node execution with metrics.

    Args:
        logger: Logger instance.
        node_name: Name of the node being executed.
        level: Log level for messages.
        include_metrics: Whether to track and log metrics.

    Yields:
        ExecutionMetrics instance for tracking.

    Example:
        >>> logger = get_logger(__name__)
        >>> with log_execution(logger, "process_data") as metrics:
        ...     # Do work
        ...     metrics.tokens_used = 100
        ...     metrics.api_calls = 2
    """
    metrics = ExecutionMetrics(node_name=node_name)

    logger.log(
        level, f"Starting execution: {node_name}", extra={"node": node_name, "event": "start"}
    )

    try:
        yield metrics

        metrics.complete(success=True)

        log_data: dict[str, Any] = {
            "node": node_name,
            "event": "complete",
            "duration": f"{metrics.duration:.2f}s",
        }

        if include_metrics:
            log_data.update(
                {
                    "tokens_used": str(metrics.tokens_used),
                    "api_calls": str(metrics.api_calls),
                }
            )

            # Update global metrics
            _METRICS_STORE["api_calls"] += metrics.api_calls
            _METRICS_STORE["total_tokens"] += metrics.tokens_used

            if node_name not in _METRICS_STORE["node_executions"]:
                _METRICS_STORE["node_executions"][node_name] = []
            _METRICS_STORE["node_executions"][node_name].append(metrics.to_dict())

        logger.log(level, f"Completed execution: {node_name}", extra=log_data)

    except Exception as e:
        metrics.complete(success=False, error=str(e))

        logger.error(
            f"Failed execution: {node_name}",
            extra={
                "node": node_name,
                "event": "error",
                "error": str(e),
                "duration": f"{metrics.duration:.2f}s" if metrics.duration else "N/A",
            },
            exc_info=True,
        )

        # Track error
        _METRICS_STORE["errors"].append(
            {
                "node": node_name,
                "error": str(e),
                "timestamp": datetime.now(timezone.utc).isoformat(),  # noqa: UP017
            }
        )

        raise


@contextmanager
def log_operation(
    logger: logging.Logger, operation: str, **context: Any
) -> Generator[None, None, None]:
    """Context manager for logging operations with context.

    Args:
        logger: Logger instance.
        operation: Operation description.
        **context: Additional context to log.

    Yields:
        None

    Example:
        >>> with log_operation(logger, "search", query="AI"):
        ...     results = search("AI")
    """
    start_time = time.time()

    logger.debug(
        f"Starting: {operation}", extra={"operation": operation, "event": "start", **context}
    )

    try:
        yield

        duration = time.time() - start_time
        logger.debug(
            f"Completed: {operation}",
            extra={
                "operation": operation,
                "event": "complete",
                "duration": f"{duration:.2f}s",
                **context,
            },
        )

    except Exception as e:
        duration = time.time() - start_time
        logger.error(
            f"Failed: {operation}",
            extra={
                "operation": operation,
                "event": "error",
                "error": str(e),
                "duration": f"{duration:.2f}s",
                **context,
            },
            exc_info=True,
        )
        raise


# Decorators for automatic logging


def log_function_call(
    logger: logging.Logger | None = None,
) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
    """Decorator to log function calls with timing.

    Args:
        logger: Optional logger instance. If None, creates one from function module.

    Returns:
        Decorated function.

    Example:
        >>> @log_function_call()
        ... def process_data(x):
        ...     return x * 2
    """

    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        nonlocal logger
        if logger is None:
            logger = get_logger(func.__module__)

        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            start_time = time.time()

            logger.debug(
                f"Calling {func.__name__}",
                extra={
                    "function": func.__name__,
                    "event": "call",
                    "args_count": len(args),
                    "kwargs_keys": list(kwargs.keys()),
                },
            )

            try:
                result = func(*args, **kwargs)

                duration = time.time() - start_time
                logger.debug(
                    f"Completed {func.__name__}",
                    extra={
                        "function": func.__name__,
                        "event": "complete",
                        "duration": f"{duration:.2f}s",
                    },
                )

                return result

            except Exception as e:
                duration = time.time() - start_time
                logger.error(
                    f"Failed {func.__name__}",
                    extra={
                        "function": func.__name__,
                        "event": "error",
                        "error": str(e),
                        "duration": f"{duration:.2f}s",
                    },
                    exc_info=True,
                )
                raise

        return wrapper

    return decorator


def log_performance(
    logger: logging.Logger | None = None, threshold_seconds: float = 1.0
) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
    """Decorator to log slow function calls.

    Only logs if execution time exceeds threshold.

    Args:
        logger: Optional logger instance.
        threshold_seconds: Minimum duration to log.

    Returns:
        Decorated function.

    Example:
        >>> @log_performance(threshold_seconds=0.5)
        ... def slow_function():
        ...     time.sleep(1)
    """

    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        nonlocal logger
        if logger is None:
            logger = get_logger(func.__module__)

        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            start_time = time.time()
            result = func(*args, **kwargs)
            duration = time.time() - start_time

            if duration >= threshold_seconds:
                logger.warning(
                    f"Slow execution: {func.__name__}",
                    extra={
                        "function": func.__name__,
                        "duration": f"{duration:.2f}s",
                        "threshold": f"{threshold_seconds:.2f}s",
                    },
                )

            return result

        return wrapper

    return decorator


# Metrics functions


def get_metrics() -> dict[str, Any]:
    """Get current metrics snapshot.

    Returns:
        Dictionary with all tracked metrics.

    Example:
        >>> metrics = get_metrics()
        >>> print(f"API calls: {metrics['api_calls']}")
    """
    metrics = _METRICS_STORE.copy()

    # Calculate total runtime
    if metrics["start_time"]:
        metrics["total_runtime"] = time.time() - metrics["start_time"]

    return metrics


def reset_metrics() -> None:
    """Reset all metrics to initial state.

    Example:
        >>> reset_metrics()
    """
    global _METRICS_STORE
    _METRICS_STORE = {
        "api_calls": 0,
        "total_tokens": 0,
        "node_executions": {},
        "errors": [],
        "start_time": time.time(),
    }


def log_metrics_summary(logger: logging.Logger) -> None:
    """Log a summary of all metrics.

    Args:
        logger: Logger instance to use.

    Example:
        >>> logger = get_logger(__name__)
        >>> log_metrics_summary(logger)
    """
    metrics = get_metrics()

    summary = {
        "total_api_calls": metrics["api_calls"],
        "total_tokens": metrics["total_tokens"],
        "total_runtime": f"{metrics.get('total_runtime', 0):.2f}s",
        "nodes_executed": len(metrics["node_executions"]),
        "errors_count": len(metrics["errors"]),
    }

    logger.info("Metrics Summary", extra=summary)

    # Log per-node statistics
    for node_name, executions in metrics["node_executions"].items():
        if executions:
            avg_duration = sum(e["duration"] for e in executions if e["duration"]) / len(executions)
            total_tokens = sum(e["tokens_used"] for e in executions)

            logger.info(
                f"Node stats: {node_name}",
                extra={
                    "node": node_name,
                    "executions": len(executions),
                    "avg_duration": f"{avg_duration:.2f}s",
                    "total_tokens": total_tokens,
                },
            )


def configure_from_config(config: dict[str, Any]) -> None:
    """Configure logging from config dictionary.

    Args:
        config: Configuration dictionary with logging settings.

    Example:
        >>> from research_assistant.config import load_config, get_logging_config
        >>> cfg = load_config()
        >>> logging_cfg = get_logging_config(cfg)
        >>> configure_from_config(logging_cfg)
    """
    setup_logging(
        level=config.get("level", "INFO"),
        structured=config.get("structured", False),
        log_file=config.get("file"),
        console=config.get("console", True),
        colored=not config.get("structured", False),
        module_levels=config.get("modules", {}),
    )
