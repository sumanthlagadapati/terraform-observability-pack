"""Type definitions for terraform_observability_pack."""

from dataclasses import dataclass, field
from typing import Any, Optional


@dataclass
class TerraformObservabilityPackOptions:
    """Configuration options for TerraformObservabilityPack.

    Attributes:
        verbose: Enable verbose logging for debugging.
        feature_1: Configuration for: Parse Terraform plan/state to discover resources and labels
        feature_2: Configuration for: Emit ready-to-apply CloudWatch alarms and dashboard JSON
        feature_3: Configuration for: Generate Prometheus scrape configs and Grafana dashboard templates
        feature_4: Configuration for: Tag-to-alert-rule mapping with override files
    """

    verbose: bool = False
    feature_1: Optional[dict[str, Any]] = None
    feature_2: Optional[dict[str, Any]] = None
    feature_3: Optional[dict[str, Any]] = None
    feature_4: Optional[dict[str, Any]] = None


@dataclass
class TerraformObservabilityPackResult:
    """Result returned by TerraformObservabilityPack operations.

    Attributes:
        success: Whether the operation succeeded.
        data: The result data, if successful.
        error: Error message, if the operation failed.
    """

    success: bool
    data: Any = field(default=None)
    error: Optional[str] = None
