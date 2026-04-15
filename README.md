# terraform_observability_pack

Generate opinionated CloudWatch/Prometheus/Grafana monitoring modules from Terraform tags and outputs.

## Installation

```bash
pip install terraform_observability_pack
```

## Quick Start

```python
from terraform_observability_pack import TerraformObservabilityPack

instance = TerraformObservabilityPack()
result = instance.run()
print(result)
```

## Features

- Parse Terraform plan/state to discover resources and labels
- Emit ready-to-apply CloudWatch alarms and dashboard JSON
- Generate Prometheus scrape configs and Grafana dashboard templates
- Tag-to-alert-rule mapping with override files

## API Reference

### `TerraformObservabilityPack`

#### Constructor

```python
TerraformObservabilityPack(options: TerraformObservabilityPackOptions | None = None)
```

#### Methods

- `run()` - Execute the main operation. Returns `TerraformObservabilityPackResult`.

## Development

```bash
# Install with dev dependencies
make install

# Run tests
make test

# Lint and type-check
make lint

# Format code
make format

# Build
make build
```

## Publishing

1. Update version in `pyproject.toml` and `src/terraform_observability_pack/__init__.py`
2. Create a GitHub release with tag `v0.x.0`
3. The GitHub Action will automatically publish to PyPI

## License

MIT
