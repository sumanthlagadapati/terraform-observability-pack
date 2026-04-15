"""Custom exceptions for terraform_observability_pack."""

from __future__ import annotations


class TerraformObservabilityPackError(Exception):
    """Base exception for all TerraformObservabilityPack errors.

    Attributes:
        message: Human-readable error description.
        code: Optional machine-readable error code.
    """

    def __init__(self, message: str, code: str | None = None) -> None:
        super().__init__(message)
        self.code = code


class ConfigurationError(TerraformObservabilityPackError):
    """Raised when the SDK is misconfigured."""


class ValidationError(TerraformObservabilityPackError):
    """Raised when input validation fails."""


class TimeoutError(TerraformObservabilityPackError):
    """Raised when an operation exceeds its time limit."""
