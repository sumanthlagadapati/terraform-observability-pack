"""Type definitions for terraform_observability_pack."""

from dataclasses import dataclass, field
from typing import Any, Optional, Dict, List


@dataclass
class TerraformResource:
    """A discovered Terraform resource and its labels/tags.

    Attributes:
        type: Resource type (e.g., aws_instance).
        name: Resource name (from Terraform config).
        labels: Key-value labels/tags discovered on the resource.
        address: Full Terraform address (e.g., module.foo.aws_instance.bar[0]).
    Example::
        TerraformResource(
            type="aws_instance",
            name="web",
            labels={"Name": "web-1", "env": "prod"},
            address="aws_instance.web[0]"
        )
    """
    type: str
    name: str
    labels: Dict[str, str]
    address: str


@dataclass
class TerraformParseResult:
    """Result of parsing a Terraform plan or state file.

    Attributes:
        resources: List of discovered resources and their labels.
        raw: The original parsed JSON input (for debugging).
    Example::
        TerraformParseResult(
            resources=[TerraformResource(...)],
            raw={...}
        )
    """
    resources: List[TerraformResource]
    raw: Any


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
