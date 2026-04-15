"""
terraform_observability_pack - Generate opinionated CloudWatch/Prometheus/Grafana monitoring modules from Terraform tags and outputs.
"""

__version__ = "0.1.0"

from .parse_terraform_planstate_to_d import TerraformObservabilityPack
from .types import TerraformObservabilityPackOptions, TerraformObservabilityPackResult
from .exceptions import TerraformObservabilityPackError, ConfigurationError, ValidationError

__all__ = [
    "TerraformObservabilityPack",
    "TerraformObservabilityPackOptions",
    "TerraformObservabilityPackResult",
    "TerraformObservabilityPackError",
    "ConfigurationError",
    "ValidationError",
]
