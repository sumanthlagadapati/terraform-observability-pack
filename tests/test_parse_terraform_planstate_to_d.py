"""Tests for terraform_observability_pack."""

from terraform_observability_pack import TerraformObservabilityPack, TerraformObservabilityPackOptions


class TestTerraformObservabilityPack:
    def test_create_instance_with_defaults(self) -> None:
        instance = TerraformObservabilityPack()
        assert instance is not None

    def test_create_instance_with_options(self) -> None:
        options = TerraformObservabilityPackOptions(verbose=True)
        instance = TerraformObservabilityPack(options)
        assert instance.options.verbose is True

    def test_run_successfully(self) -> None:
        instance = TerraformObservabilityPack()
        result = instance.run()
        assert result.success is True
        assert result.data is not None

    def test_run_returns_result_type(self) -> None:
        instance = TerraformObservabilityPack()
        result = instance.run()
        assert result.error is None
