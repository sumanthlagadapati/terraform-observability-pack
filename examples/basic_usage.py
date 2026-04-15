#!/usr/bin/env python3
"""Basic usage example for terraform_observability_pack."""

from terraform_observability_pack import TerraformObservabilityPack, TerraformObservabilityPackOptions


def main() -> None:
    # Create with default options
    instance = TerraformObservabilityPack()
    result = instance.run()
    print(f"Default run: success={result.success}, data={result.data}")

    # Create with custom options
    options = TerraformObservabilityPackOptions(verbose=True)
    instance = TerraformObservabilityPack(options)
    result = instance.run()
    print(f"Verbose run: success={result.success}, data={result.data}")


if __name__ == "__main__":
    main()
