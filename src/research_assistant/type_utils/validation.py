"""Runtime type validation utilities.

This module provides utilities for runtime type checking and validation,
complementing Pydantic models with additional validation logic.

Example:
    >>> from research_assistant.type_utils.validation import validate_type, TypeValidator
    >>>
    >>> validate_type(42, int)  # True
    >>> validate_type("hello", int)  # Raises TypeError
"""

import inspect
from collections.abc import Callable
from functools import wraps
from typing import Any, ParamSpec, TypeVar, Union, get_args, get_origin

from pydantic import BaseModel, ValidationError

P = ParamSpec("P")
R = TypeVar("R")


def validate_type(value: Any, expected_type: type, param_name: str = "value") -> bool:
    """Validate that a value matches an expected type.

    Args:
        value: Value to validate.
        expected_type: Expected type.
        param_name: Parameter name for error messages.

    Returns:
        True if valid.

    Raises:
        TypeError: If value doesn't match expected type.

    Example:
        >>> validate_type(42, int, "age")
        True
    """
    # Handle None
    if value is None:
        origin = get_origin(expected_type)
        if origin is Union:
            args = get_args(expected_type)
            if type(None) in args:
                return True
        raise TypeError(f"{param_name} cannot be None")

    # Handle Union types (including Optional)
    origin = get_origin(expected_type)
    if origin is Union:
        args = get_args(expected_type)
        for arg in args:
            if arg is type(None):
                continue
            try:
                validate_type(value, arg, param_name)
                return True
            except TypeError:
                continue
        raise TypeError(f"{param_name} must be one of {args}, got {type(value).__name__}")

    # Handle List types
    if origin is list:
        if not isinstance(value, list):
            raise TypeError(f"{param_name} must be a list, got {type(value).__name__}")
        args = get_args(expected_type)
        if args:
            for i, item in enumerate(value):
                validate_type(item, args[0], f"{param_name}[{i}]")
        return True

    # Handle Dict types
    if origin is dict:
        if not isinstance(value, dict):
            raise TypeError(f"{param_name} must be a dict, got {type(value).__name__}")
        return True

    # Handle regular types
    if not isinstance(value, expected_type):
        raise TypeError(
            f"{param_name} must be {expected_type.__name__}, " f"got {type(value).__name__}"
        )

    return True


def validate_function_args(func: Callable[P, R]) -> Callable[P, R]:
    """Decorator to validate function arguments against type hints.

    Args:
        func: Function to decorate.

    Returns:
        Decorated function with argument validation.

    Example:
        >>> @validate_function_args
        ... def greet(name: str, age: int) -> str:
        ...     return f"Hello {name}, age {age}"
        >>>
        >>> greet("Alice", 30)  # OK
        >>> greet("Alice", "30")  # Raises TypeError
    """
    sig = inspect.signature(func)

    @wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        # Bind arguments
        bound = sig.bind(*args, **kwargs)
        bound.apply_defaults()

        # Validate each argument
        for param_name, param_value in bound.arguments.items():
            param = sig.parameters[param_name]

            # Skip if no annotation
            if param.annotation == inspect.Parameter.empty:
                continue

            # Validate type
            try:
                validate_type(param_value, param.annotation, param_name)
            except TypeError as e:
                raise TypeError(f"Invalid argument in {func.__name__}(): {str(e)}") from e

        return func(*args, **kwargs)

    return wrapper


class TypeValidator:
    """Reusable type validator with custom rules.

    Example:
        >>> validator = TypeValidator()
        >>> validator.add_rule("positive_int", lambda x: isinstance(x, int) and x > 0)
        >>> validator.validate(42, "positive_int")  # True
        >>> validator.validate(-5, "positive_int")  # Raises ValueError
    """

    def __init__(self) -> None:
        """Initialize type validator."""
        self.rules: dict[str, Callable[[Any], bool]] = {}
        self.error_messages: dict[str, str] = {}

    def add_rule(
        self, name: str, validator: Callable[[Any], bool], error_message: str | None = None
    ) -> None:
        """Add a validation rule.

        Args:
            name: Rule name.
            validator: Validation function returning bool.
            error_message: Optional custom error message.
        """
        self.rules[name] = validator
        if error_message:
            self.error_messages[name] = error_message

    def validate(self, value: Any, rule_name: str) -> bool:
        """Validate a value against a rule.

        Args:
            value: Value to validate.
            rule_name: Name of rule to use.

        Returns:
            True if valid.

        Raises:
            ValueError: If validation fails.
            KeyError: If rule doesn't exist.
        """
        if rule_name not in self.rules:
            raise KeyError(f"Unknown validation rule: {rule_name}")

        if not self.rules[rule_name](value):
            error_msg = self.error_messages.get(
                rule_name, f"Validation failed for rule: {rule_name}"
            )
            raise ValueError(error_msg)

        return True


# Common validators


def validate_non_empty_string(value: str, param_name: str = "value") -> bool:
    """Validate that a string is non-empty.

    Args:
        value: String to validate.
        param_name: Parameter name for error messages.

    Returns:
        True if valid.

    Raises:
        ValueError: If string is empty.
    """
    if not isinstance(value, str):
        raise TypeError(f"{param_name} must be a string")

    if not value or not value.strip():
        raise ValueError(f"{param_name} cannot be empty")

    return True


def validate_positive_number(value: int | float, param_name: str = "value") -> bool:
    """Validate that a number is positive.

    Args:
        value: Number to validate.
        param_name: Parameter name for error messages.

    Returns:
        True if valid.

    Raises:
        ValueError: If number is not positive.
    """
    if not isinstance(value, int | float):
        raise TypeError(f"{param_name} must be a number")

    if value <= 0:
        raise ValueError(f"{param_name} must be positive, got {value}")

    return True


def validate_range(
    value: int | float,
    min_val: int | float | None = None,
    max_val: int | float | None = None,
    param_name: str = "value",
) -> bool:
    """Validate that a number is within a range.

    Args:
        value: Number to validate.
        min_val: Minimum value (inclusive).
        max_val: Maximum value (inclusive).
        param_name: Parameter name for error messages.

    Returns:
        True if valid.

    Raises:
        ValueError: If number is out of range.
    """
    if not isinstance(value, int | float):
        raise TypeError(f"{param_name} must be a number")

    if min_val is not None and value < min_val:
        raise ValueError(f"{param_name} must be >= {min_val}, got {value}")

    if max_val is not None and value > max_val:
        raise ValueError(f"{param_name} must be <= {max_val}, got {value}")

    return True


def validate_list_length(
    value: list[Any],
    min_length: int | None = None,
    max_length: int | None = None,
    param_name: str = "value",
) -> bool:
    """Validate list length.

    Args:
        value: List to validate.
        min_length: Minimum length.
        max_length: Maximum length.
        param_name: Parameter name for error messages.

    Returns:
        True if valid.

    Raises:
        ValueError: If list length is invalid.
    """
    if not isinstance(value, list):
        raise TypeError(f"{param_name} must be a list")

    length = len(value)

    if min_length is not None and length < min_length:
        raise ValueError(f"{param_name} must have at least {min_length} items, got {length}")

    if max_length is not None and length > max_length:
        raise ValueError(f"{param_name} must have at most {max_length} items, got {length}")

    return True


def validate_dict_keys(
    value: dict[str, Any],
    required_keys: list[str] | None = None,
    optional_keys: list[str] | None = None,
    param_name: str = "value",
) -> bool:
    """Validate dictionary keys.

    Args:
        value: Dictionary to validate.
        required_keys: Keys that must be present.
        optional_keys: Additional allowed keys.
        param_name: Parameter name for error messages.

    Returns:
        True if valid.

    Raises:
        ValueError: If required keys are missing or invalid keys present.
    """
    if not isinstance(value, dict):
        raise TypeError(f"{param_name} must be a dictionary")

    # Check required keys
    if required_keys:
        missing = set(required_keys) - set(value.keys())
        if missing:
            raise ValueError(f"{param_name} missing required keys: {', '.join(missing)}")

    # Check for invalid keys
    if required_keys or optional_keys:
        allowed = set(required_keys or []) | set(optional_keys or [])
        invalid = set(value.keys()) - allowed
        if invalid:
            raise ValueError(f"{param_name} has invalid keys: {', '.join(invalid)}")

    return True


# Pydantic integration


def validate_pydantic_model(
    data: dict[str, Any],
    model_class: type[BaseModel],
) -> BaseModel:
    """Validate data against a Pydantic model.

    Args:
        data: Data to validate.
        model_class: Pydantic model class.

    Returns:
        Validated model instance.

    Raises:
        ValidationError: If validation fails.

    Example:
        >>> from research_assistant.core.schemas import Analyst
        >>> data = {"name": "Alice", "role": "Researcher", ...}
        >>> analyst = validate_pydantic_model(data, Analyst)
    """
    try:
        return model_class(**data)
    except ValidationError as e:
        # Re-raise with more context
        raise ValueError(f"Validation error for {model_class.__name__}: {e}") from e
