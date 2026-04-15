"""Internal utilities for terraform_observability_pack."""

from __future__ import annotations

import functools
import time
from typing import Any, Callable, TypeVar

from .exceptions import TerraformObservabilityPackError

T = TypeVar("T")


def retry(
    max_attempts: int = 3,
    delay: float = 1.0,
    exceptions: tuple[type[Exception], ...] = (TerraformObservabilityPackError,),
) -> Callable[[Callable[..., T]], Callable[..., T]]:
    """Retry a function with exponential backoff.

    Args:
        max_attempts: Maximum number of attempts.
        delay: Initial delay in seconds between retries.
        exceptions: Exception types that trigger a retry.
    """

    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> T:
            last_error: Exception | None = None
            for attempt in range(max_attempts):
                try:
                    return func(*args, **kwargs)
                except exceptions as exc:
                    last_error = exc
                    if attempt < max_attempts - 1:
                        time.sleep(delay * (2**attempt))
            raise last_error  # type: ignore[misc]

        return wrapper

    return decorator


def validate_not_empty(value: str, field_name: str) -> str:
    """Validate that a string value is not empty.

    Raises:
        ValidationError: If the value is empty or whitespace-only.
    """
    from .exceptions import ValidationError

    stripped = value.strip()
    if not stripped:
        raise ValidationError(
            f"{field_name} must not be empty", code="EMPTY_FIELD"
        )
    return stripped
