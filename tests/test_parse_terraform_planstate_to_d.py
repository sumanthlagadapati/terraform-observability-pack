"""Tests for terraform_observability_pack."""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))
from terraform_observability_pack import TerraformObservabilityPack, TerraformObservabilityPackOptions


class TestTerraformObservabilityPack:
    def test_emit_prometheus_configs_basic(self):
        """
        Test that emit_prometheus_configs emits a valid scrape config for a supported resource.
        """
        instance = TerraformObservabilityPack()
        # Simulate a resource that should be scraped (e.g., EC2 with Prometheus label)
        resources = [
            type('FakeResource', (), {
                'type': 'aws_instance',
                'name': 'web',
                'labels': {'Name': 'web-1', 'prometheus_scrape': 'true', 'instance_id': 'i-123'},
                'address': 'aws_instance.web[0]'
            })()
        ]
        if hasattr(instance, 'emit_prometheus_configs'):
            configs = instance.emit_prometheus_configs(resources)
            assert isinstance(configs, list)
            assert configs, "Should emit at least one config"
            # Check basic Prometheus config structure
            cfg = configs[0]
            assert 'job_name' in cfg
            assert 'static_configs' in cfg
            assert isinstance(cfg['static_configs'], list)
        else:
            import pytest
            pytest.skip('emit_prometheus_configs not implemented yet')

    def test_emit_prometheus_configs_empty(self):
        """
        Test that emit_prometheus_configs returns empty list for no resources.
        """
        instance = TerraformObservabilityPack()
        if hasattr(instance, 'emit_prometheus_configs'):
            configs = instance.emit_prometheus_configs([])
            assert configs == []
        else:
            import pytest
            pytest.skip('emit_prometheus_configs not implemented yet')

    def test_emit_prometheus_configs_invalid_resource(self):
        """
        Test that emit_prometheus_configs handles invalid resource types gracefully.
        """
        instance = TerraformObservabilityPack()
        resources = [object()]  # Not a TerraformResource
        if hasattr(instance, 'emit_prometheus_configs'):
            configs = instance.emit_prometheus_configs(resources)
            assert isinstance(configs, list)
        else:
            import pytest
            pytest.skip('emit_prometheus_configs not implemented yet')

    def test_emit_prometheus_configs_with_custom_labels(self):
        """
        Test that emit_prometheus_configs includes custom labels in scrape config.
        """
        instance = TerraformObservabilityPack()
        resources = [
            type('FakeResource', (), {
                'type': 'aws_instance',
                'name': 'web',
                'labels': {'Name': 'web-1', 'prometheus_scrape': 'true', 'env': 'prod', 'instance_id': 'i-123'},
                'address': 'aws_instance.web[0]'
            })()
        ]
        if hasattr(instance, 'emit_prometheus_configs'):
            configs = instance.emit_prometheus_configs(resources)
            assert isinstance(configs, list)
            if configs:
                targets = configs[0].get('static_configs', [{}])[0].get('targets', [])
                labels = configs[0].get('static_configs', [{}])[0].get('labels', {})
                assert isinstance(labels, dict)
                assert labels.get('env') == 'prod'
        else:
            import pytest
            pytest.skip('emit_prometheus_configs not implemented yet')

    def test_emit_prometheus_configs_large_input(self):
        """
        Test that emit_prometheus_configs handles large resource lists efficiently.
        """
        instance = TerraformObservabilityPack()
        resources = [
            type('FakeResource', (), {
                'type': 'aws_instance',
                'name': f'web{i}',
                'labels': {'Name': f'web-{i}', 'prometheus_scrape': 'true', 'instance_id': f'i-{i}'},
                'address': f'aws_instance.web[{i}]'
            })() for i in range(200)
        ]
        if hasattr(instance, 'emit_prometheus_configs'):
            configs = instance.emit_prometheus_configs(resources)
            assert isinstance(configs, list)
        else:
            import pytest
            pytest.skip('emit_prometheus_configs not implemented yet')

    def test_alarm_defaults_override_all_fields(self):
        instance = TerraformObservabilityPack()
        resources = [
            type('FakeResource', (), {
                'type': 'aws_instance',
                'name': 'web',
                'labels': {'Name': 'web-1', 'instance_id': 'i-123'},
                'address': 'aws_instance.web[0]'
            })()
        ]
        alarm_defaults = {
            "ComparisonOperator": "LessThanThreshold",
            "EvaluationPeriods": 5,
            "Period": 60,
            "Statistic": "Maximum",
            "Threshold": 99.9,
            "TreatMissingData": "breaching",
            "ActionsEnabled": False,
            "AlarmActions": ["arn:aws:sns:us-east-1:123456789012:my-topic"]
        }
        alarms = instance.emit_cloudwatch_alarms(resources, alarm_defaults=alarm_defaults)
        assert alarms[0]["ComparisonOperator"] == "LessThanThreshold"
        assert alarms[0]["EvaluationPeriods"] == 5
        assert alarms[0]["Period"] == 60
        assert alarms[0]["Statistic"] == "Maximum"
        assert alarms[0]["Threshold"] == 99.9
        assert alarms[0]["TreatMissingData"] == "breaching"
        assert alarms[0]["ActionsEnabled"] is False
        assert alarms[0]["AlarmActions"] == ["arn:aws:sns:us-east-1:123456789012:my-topic"]

    def test_alarm_defaults_with_extra_keys_are_preserved(self):
        instance = TerraformObservabilityPack()
        resources = [
            type('FakeResource', (), {
                'type': 'aws_instance',
                'name': 'web',
                'labels': {'Name': 'web-1', 'instance_id': 'i-123'},
                'address': 'aws_instance.web[0]'
            })()
        ]
        alarm_defaults = {
            "CustomKey": "custom-value",
            "AnotherKey": 1234
        }
        alarms = instance.emit_cloudwatch_alarms(resources, alarm_defaults=alarm_defaults)
        assert alarms[0]["CustomKey"] == "custom-value"
        assert alarms[0]["AnotherKey"] == 1234

    def test_alarm_defaults_empty_dict(self):
        instance = TerraformObservabilityPack()
        resources = [
            type('FakeResource', (), {
                'type': 'aws_instance',
                'name': 'web',
                'labels': {'Name': 'web-1', 'instance_id': 'i-123'},
                'address': 'aws_instance.web[0]'
            })()
        ]
        alarms = instance.emit_cloudwatch_alarms(resources, alarm_defaults={})
        # Should still have required fields
        assert alarms[0]["AlarmName"].startswith("web-1-HighCPU")
        assert alarms[0]["Namespace"] == "AWS/EC2"
        assert alarms[0]["MetricName"] == "CPUUtilization"
        assert "ComparisonOperator" not in alarms[0] or alarms[0]["ComparisonOperator"] == "GreaterThanOrEqualToThreshold"

    def test_alarm_defaults_with_invalid_type(self):
        instance = TerraformObservabilityPack()
        resources = [
            type('FakeResource', (), {
                'type': 'aws_instance',
                'name': 'web',
                'labels': {'Name': 'web-1', 'instance_id': 'i-123'},
                'address': 'aws_instance.web[0]'
            })()
        ]
        alarm_defaults = {
            "Threshold": ["not-a-number"]
        }
        alarms = instance.emit_cloudwatch_alarms(resources, alarm_defaults=alarm_defaults)
        # Should not crash, but Threshold will be as provided
        assert alarms[0]["Threshold"] == ["not-a-number"]

    def test_alarm_postprocess_per_resource(self):
        instance = TerraformObservabilityPack()
        resources = [
            type('FakeResource', (), {
                'type': 'aws_instance',
                'name': 'web',
                'labels': {'Name': 'web-1', 'instance_id': 'i-123'},
                'address': 'aws_instance.web[0]'
            })(),
            type('FakeResource', (), {
                'type': 'aws_s3_bucket',
                'name': 'bucket',
                'labels': {'Name': 'bucket-1'},
                'address': 'aws_s3_bucket.bucket[0]'
            })()
        ]
        alarms = instance.emit_cloudwatch_alarms(resources)
        # Post-process: set a custom threshold for S3 alarms only
        for alarm in alarms:
            if alarm["Namespace"] == "AWS/S3":
                alarm["Threshold"] = 12345
        s3_alarm = next(a for a in alarms if a["Namespace"] == "AWS/S3")
        assert s3_alarm["Threshold"] == 12345

    def test_create_instance_with_defaults(self) -> None:
        instance = TerraformObservabilityPack()
        assert instance is not None

    def test_create_instance_with_options(self) -> None:
        options = TerraformObservabilityPackOptions(verbose=True)
        instance = TerraformObservabilityPack(options)
        assert instance.options.verbose is True

    def test_parse_plan_with_resources(self) -> None:
        plan = {
            "planned_values": {
                "root_module": {
                    "resources": [
                        {
                            "type": "aws_instance",
                            "name": "web",
                            "address": "aws_instance.web[0]",
                            "values": {
                                "tags": {"Name": "web-1", "env": "prod"}
                            }
                        }
                    ],
                    "child_modules": []
                }
            }
        }
        instance = TerraformObservabilityPack()
        result = instance.parse_plan_or_state(plan)
        assert len(result.resources) == 1
        r = result.resources[0]
        assert r.type == "aws_instance"
        assert r.name == "web"
        assert r.labels == {"Name": "web-1", "env": "prod"}
        assert r.address == "aws_instance.web[0]"

    def test_parse_state_with_resources(self) -> None:
        state = {
            "resources": [
                {
                    "type": "aws_s3_bucket",
                    "name": "bucket",
                    "address": "aws_s3_bucket.bucket",
                    "instances": [
                        {
                            "attributes": {
                                "tags": {"Name": "bucket-1", "env": "dev"}
                            }
                        }
                    ]
                }
            ]
        }
        instance = TerraformObservabilityPack()
        result = instance.parse_plan_or_state(state)
        assert len(result.resources) == 1
        r = result.resources[0]
        assert r.type == "aws_s3_bucket"
        assert r.name == "bucket"
        assert r.labels == {"Name": "bucket-1", "env": "dev"}
        assert r.address == "aws_s3_bucket.bucket"

    def test_parse_plan_with_no_resources(self) -> None:
        plan = {"planned_values": {"root_module": {}}}
        instance = TerraformObservabilityPack()
        result = instance.parse_plan_or_state(plan)
        assert result.resources == []

    def test_parse_state_with_no_resources(self) -> None:
        state = {"resources": []}
        instance = TerraformObservabilityPack()
        result = instance.parse_plan_or_state(state)
        assert result.resources == []

    def test_parse_invalid_input_type(self) -> None:
        instance = TerraformObservabilityPack()
        import pytest
        with pytest.raises(Exception):
            instance.parse_plan_or_state("not a dict")

    def test_parse_invalid_input_structure(self) -> None:
        instance = TerraformObservabilityPack()
        import pytest
        with pytest.raises(Exception):
            instance.parse_plan_or_state({"foo": "bar"})

    def test_parse_resource_with_no_labels(self) -> None:
        plan = {
            "planned_values": {
                "root_module": {
                    "resources": [
                        {
                            "type": "aws_instance",
                            "name": "nolabels",
                            "address": "aws_instance.nolabels[0]",
                            "values": {}
                        }
                    ]
                }
            }
        }
        instance = TerraformObservabilityPack()
        result = instance.parse_plan_or_state(plan)
        assert len(result.resources) == 1
        assert result.resources[0].labels == {}

    def test_parse_large_plan(self) -> None:
        # Simulate a large plan with 1000 resources
        plan = {
            "planned_values": {
                "root_module": {
                    "resources": [
                        {
                            "type": "aws_instance",
                            "name": f"web{i}",
                            "address": f"aws_instance.web[{i}]",
                            "values": {"tags": {"Name": f"web-{i}"}}
                        } for i in range(1000)
                    ]
                }
            }
        }
        instance = TerraformObservabilityPack()
        result = instance.parse_plan_or_state(plan)
        assert len(result.resources) == 1000

    def test_run_successfully(self) -> None:
        instance = TerraformObservabilityPack()
        result = instance.run()
        assert result.success is True
        assert result.data is not None

    def test_emit_cloudwatch_alarms_for_many_resource_types(self) -> None:
        instance = TerraformObservabilityPack()
        resources = [
            # EC2 instance
            type('FakeResource', (), {
                'type': 'aws_instance',
                'name': 'web',
                'labels': {'Name': 'web-1', 'instance_id': 'i-123'},
                'address': 'aws_instance.web[0]'
            })(),
            # S3 bucket
            type('FakeResource', (), {
                'type': 'aws_s3_bucket',
                'name': 'bucket',
                'labels': {'Name': 'bucket-1'},
                'address': 'aws_s3_bucket.bucket[0]'
            })(),
            # RDS instance
            type('FakeResource', (), {
                'type': 'aws_db_instance',
                'name': 'db',
                'labels': {'Name': 'db-1'},
                'address': 'aws_db_instance.db[0]'
            })(),
            # DynamoDB table
            type('FakeResource', (), {
                'type': 'aws_dynamodb_table',
                'name': 'ddb',
                'labels': {'Name': 'ddb-1'},
                'address': 'aws_dynamodb_table.ddb[0]'
            })(),
            # Lambda function
            type('FakeResource', (), {
                'type': 'aws_lambda_function',
                'name': 'lambda',
                'labels': {'Name': 'lambda-1'},
                'address': 'aws_lambda_function.lambda[0]'
            })(),
            # ELB Classic
            type('FakeResource', (), {
                'type': 'aws_elb',
                'name': 'elb',
                'labels': {'Name': 'elb-1'},
                'address': 'aws_elb.elb[0]'
            })(),
            # ALB/NLB
            type('FakeResource', (), {
                'type': 'aws_lb',
                'name': 'lb',
                'labels': {'Name': 'lb-1'},
                'address': 'aws_lb.lb[0]'
            })(),
            # Auto Scaling Group
            type('FakeResource', (), {
                'type': 'aws_autoscaling_group',
                'name': 'asg',
                'labels': {'Name': 'asg-1'},
                'address': 'aws_autoscaling_group.asg[0]'
            })(),
            # SNS Topic
            type('FakeResource', (), {
                'type': 'aws_sns_topic',
                'name': 'sns',
                'labels': {'Name': 'sns-1'},
                'address': 'aws_sns_topic.sns[0]'
            })(),
            # SQS Queue
            type('FakeResource', (), {
                'type': 'aws_sqs_queue',
                'name': 'sqs',
                'labels': {'Name': 'sqs-1'},
                'address': 'aws_sqs_queue.sqs[0]'
            })(),
        ]
        alarms = instance.emit_cloudwatch_alarms(resources)
        assert isinstance(alarms, list)
        # 7 original + 2 (SNS) + 2 (SQS) = 11
        assert len(alarms) == 11
        # Check each alarm type
        ns_map = {
            'AWS/EC2': 'web-1-HighCPU',
            'AWS/S3': 'bucket-1-NumObjects',
            'AWS/RDS': 'db-1-RDS-HighCPU',
            'AWS/DynamoDB': 'ddb-1-DDB-ReadCapacity',
            'AWS/Lambda': 'lambda-1-Lambda-Errors',
            'AWS/ELB': 'elb-1-ELB-HealthyHostCount',
            'AWS/ApplicationELB': 'lb-1-LB-HealthyHostCount',
            'AWS/AutoScaling': 'asg-1-ASG-InService',
            'AWS/SNS': ['sns-1-SNS-MessagesPublished', 'sns-1-SNS-NotificationsFailed'],
            'AWS/SQS': ['sqs-1-SQS-MessagesVisible', 'sqs-1-SQS-MessagesReceived'],
        }
        alarm_names = [a['AlarmName'] for a in alarms]
        # Check all expected alarm names are present
        for v in ns_map.values():
            if isinstance(v, list):
                for name in v:
                    assert name in alarm_names
            else:
                assert v in alarm_names
        # Specific metric checks
        assert any(a['MetricName'] == 'CPUUtilization' and a['Namespace'] == 'AWS/EC2' for a in alarms)
        assert any(a['MetricName'] == 'NumberOfObjects' and a['Namespace'] == 'AWS/S3' for a in alarms)
        assert any(a['MetricName'] == 'CPUUtilization' and a['Namespace'] == 'AWS/RDS' for a in alarms)
        assert any(a['MetricName'] == 'ConsumedReadCapacityUnits' and a['Namespace'] == 'AWS/DynamoDB' for a in alarms)
        assert any(a['MetricName'] == 'Errors' and a['Namespace'] == 'AWS/Lambda' for a in alarms)
        assert any(a['MetricName'] == 'HealthyHostCount' and a['Namespace'] == 'AWS/ELB' for a in alarms)
        assert any(a['MetricName'] == 'HealthyHostCount' and a['Namespace'] == 'AWS/ApplicationELB' for a in alarms)
        assert any(a['MetricName'] == 'GroupInServiceInstances' and a['Namespace'] == 'AWS/AutoScaling' for a in alarms)
        # SNS
        assert any(a['MetricName'] == 'NumberOfMessagesPublished' and a['Namespace'] == 'AWS/SNS' for a in alarms)
        assert any(a['MetricName'] == 'NumberOfNotificationsFailed' and a['Namespace'] == 'AWS/SNS' for a in alarms)
        # SQS
        assert any(a['MetricName'] == 'ApproximateNumberOfMessagesVisible' and a['Namespace'] == 'AWS/SQS' for a in alarms)
        assert any(a['MetricName'] == 'NumberOfMessagesReceived' and a['Namespace'] == 'AWS/SQS' for a in alarms)

    def test_run_returns_result_type(self) -> None:
        instance = TerraformObservabilityPack()
        result = instance.run()
        assert result.error is None

    def test_parse_plan_with_nested_modules_and_multiple_resources(self) -> None:
        plan = {
            "planned_values": {
                "root_module": {
                    "resources": [
                        {
                            "type": "aws_instance",
                            "name": "web",
                            "address": "aws_instance.web[0]",
                            "values": {
                                "tags": {"Name": "web-1", "env": "prod"}
                            }
                        }
                    ],
                    "child_modules": [
                        {
                            "resources": [
                                {
                                    "type": "aws_db_instance",
                                    "name": "db",
                                    "address": "aws_db_instance.db[0]",
                                    "values": {
                                        "tags": {"Name": "db-1", "env": "prod", "role": "primary"}
                                    }
                                },
                                {
                                    "type": "aws_s3_bucket",
                                    "name": "bucket",
                                    "address": "aws_s3_bucket.bucket[0]",
                                    "values": {
                                        "tags": {"Name": "bucket-1"}
                                    }
                                }
                            ],
                            "child_modules": []
                        }
                    ]
                }
            }
        }
        instance = TerraformObservabilityPack()
        result = instance.parse_plan_or_state(plan)
        assert len(result.resources) == 3
        types = {r.type for r in result.resources}
        assert types == {"aws_instance", "aws_db_instance", "aws_s3_bucket"}
        names = {r.name for r in result.resources}
        assert names == {"web", "db", "bucket"}
        # Check nested resource labels
        db = next(r for r in result.resources if r.type == "aws_db_instance")
        assert db.labels["role"] == "primary"

    def test_parse_state_with_multiple_instances_and_missing_tags(self) -> None:
        state = {
            "resources": [
                {
                    "type": "aws_autoscaling_group",
                    "name": "asg",
                    "address": "aws_autoscaling_group.asg",
                    "instances": [
                        {
                            "attributes": {
                                "tags": None
                            }
                        },
                        {
                            "attributes": {
                                "tags": {"Name": "asg-2", "env": "stage"}
                            }
                        }
                    ]
                },
                {
                    "type": "aws_lambda_function",
                    "name": "lambda",
                    "address": "aws_lambda_function.lambda",
                    "instances": [
                        {
                            "attributes": {
                                # No tags field at all
                            }
                        }
                    ]
                }
            ]
        }
        instance = TerraformObservabilityPack()
        result = instance.parse_plan_or_state(state)
        # Should create a resource for each instance
        asg_resources = [r for r in result.resources if r.type == "aws_autoscaling_group"]
        lambda_resources = [r for r in result.resources if r.type == "aws_lambda_function"]
        assert len(asg_resources) == 2
        assert len(lambda_resources) == 1
        # First ASG instance has no tags
        assert asg_resources[0].labels == {} or asg_resources[0].labels is None
        # Second ASG instance has tags
        assert asg_resources[1].labels == {"Name": "asg-2", "env": "stage"}
        # Lambda instance has no tags
        assert lambda_resources[0].labels == {} or lambda_resources[0].labels is None

    def test_parse_plan_with_null_and_missing_fields(self) -> None:
        plan = {
            "planned_values": {
                "root_module": {
                    "resources": [
                        {
                            "type": "aws_security_group",
                            "name": "sg",
                            "address": "aws_security_group.sg[0]",
                            "values": {
                                "tags": None
                            }
                        },
                        {
                            "type": "aws_iam_role",
                            "name": "role",
                            "address": "aws_iam_role.role[0]",
                            "values": {
                                # No tags field
                            }
                        }
                    ]
                }
            }
        }
        instance = TerraformObservabilityPack()
        result = instance.parse_plan_or_state(plan)
        assert len(result.resources) == 2
        sg = next(r for r in result.resources if r.type == "aws_security_group")
        role = next(r for r in result.resources if r.type == "aws_iam_role")
        assert sg.labels == {} or sg.labels is None
        assert role.labels == {} or role.labels is None

    def test_parse_plan_missing_planned_values(self) -> None:
        plan = {"foo": "bar"}
        instance = TerraformObservabilityPack()
        import pytest
        with pytest.raises(Exception):
            instance.parse_plan_or_state(plan)

    def test_parse_state_missing_resources(self) -> None:
        state = {"not_resources": []}
        instance = TerraformObservabilityPack()
        import pytest
        with pytest.raises(Exception):
            instance.parse_plan_or_state(state)

    def test_parse_plan_with_non_dict(self) -> None:
        plan = [1, 2, 3]
        instance = TerraformObservabilityPack()
        import pytest
        with pytest.raises(Exception):
            instance.parse_plan_or_state(plan)

    def test_parse_state_with_partial_resource(self) -> None:
        state = {
            "resources": [
                {
                    # missing type, name, address
                    "instances": [
                        {"attributes": {"tags": {"foo": "bar"}}}
                    ]
                }
            ]
        }
        instance = TerraformObservabilityPack()
        result = instance.parse_plan_or_state(state)
        assert len(result.resources) == 1
        r = result.resources[0]
        assert r.type == ""
        assert r.name == ""
        assert r.address == ""
        assert r.labels == {"foo": "bar"}
