"""Core module for terraform_observability_pack."""

from .types import TerraformObservabilityPackOptions, TerraformObservabilityPackResult


class TerraformObservabilityPack:
    """Generate opinionated CloudWatch/Prometheus/Grafana monitoring modules from Terraform tags and outputs.

    Example::

        from terraform_observability_pack import TerraformObservabilityPack
        instance = TerraformObservabilityPack()
        result = instance.parse_plan_or_state(plan_or_state_json)
        for resource in result.resources:
            print(resource.type, resource.name, resource.labels)

        # Emit CloudWatch alarms JSON
        alarms_json = instance.emit_cloudwatch_alarms(result.resources)
        print(alarms_json)
    """

    def __init__(self, options: TerraformObservabilityPackOptions | None = None) -> None:
        self.options = options or TerraformObservabilityPackOptions()

    def parse_plan_or_state(self, plan_or_state: dict) -> 'TerraformParseResult':
        """Parse a Terraform plan or state JSON to discover resources and labels.

        Args:
            plan_or_state: Parsed JSON from a Terraform plan or state file.

        Returns:
            TerraformParseResult: Discovered resources and their labels.

        Raises:
            ValidationError: If input is not a valid Terraform plan/state.

        Example::
            with open('terraform.tfstate') as f:
                data = json.load(f)
            pack = TerraformObservabilityPack()
            result = pack.parse_plan_or_state(data)
            for r in result.resources:
                print(r.type, r.name, r.labels)
        """
        from .types import TerraformResource, TerraformParseResult
        from .exceptions import ValidationError

        if not isinstance(plan_or_state, dict):
            raise ValidationError("Input must be a dict (parsed JSON)")

        resources = []
        # Detect if this is a plan or state file
        if "planned_values" in plan_or_state:  # Plan file
            root = plan_or_state.get("planned_values", {}).get("root_module", {})
            resources += self._extract_resources_from_module(root)
            for child in root.get("child_modules", []):
                resources += self._extract_resources_from_module(child)
        elif "resources" in plan_or_state:  # State file
            for res in plan_or_state["resources"]:
                # Handle multiple instances per resource
                for instance in res.get("instances", []):
                    resources.append(self._resource_from_state_instance(res, instance))
        else:
            raise ValidationError("Input is not a valid Terraform plan or state file")

        return TerraformParseResult(resources=resources, raw=plan_or_state)

    def _extract_resources_from_module(self, module: dict) -> list:
        from .types import TerraformResource
        resources = []
        for res in module.get("resources", []):
            attrs = res.get("values", {})
            labels = attrs.get("tags", attrs.get("labels", {}))
            if not isinstance(labels, dict):
                labels = {}
            resources.append(TerraformResource(
                type=res.get("type", ""),
                name=res.get("name", ""),
                labels=labels,
                address=res.get("address", "")
            ))
        return resources

    def _resource_from_state_instance(self, res: dict, instance: dict):
        from .types import TerraformResource
        attrs = instance.get("attributes", {})
        labels = attrs.get("tags", attrs.get("labels", {}))
        if not isinstance(labels, dict):
            labels = {}
        return TerraformResource(
            type=res.get("type", ""),
            name=res.get("name", ""),
            labels=labels,
            address=res.get("address", "")
        )

    def emit_cloudwatch_alarms(self, resources: list, alarm_defaults: dict | None = None) -> list:
        """
        Emit ready-to-apply CloudWatch alarm JSON definitions for the given resources.

        Args:
            resources: List of TerraformResource objects (from parse_plan_or_state).
            alarm_defaults: Optional dict of default alarm parameters (applied to all alarms).

        Returns:
            List of CloudWatch alarm JSON objects (dicts).

        Example::
            alarms = instance.emit_cloudwatch_alarms(result.resources)
            for alarm in alarms:
                print(json.dumps(alarm, indent=2))
        """
        from .types import TerraformResource
        import copy
        import json

        if alarm_defaults is None:
            alarm_defaults = {
                "ComparisonOperator": "GreaterThanOrEqualToThreshold",
                "EvaluationPeriods": 1,
                "Period": 300,
                "Statistic": "Average",
                "Threshold": 1.0,
                "TreatMissingData": "missing",
                "ActionsEnabled": True,
            }

        alarms = []
        for resource in resources:
            if not isinstance(resource, TerraformResource):
                continue
            # Example: emit CPUUtilization alarm for EC2 instances
            if resource.type == "aws_instance":
                alarm = copy.deepcopy(alarm_defaults)
                alarm.update({
                    "AlarmName": f"{resource.labels.get('Name', resource.name)}-HighCPU",
                    "AlarmDescription": f"High CPU for {resource.labels.get('Name', resource.name)} ({resource.address})",
                    "Namespace": "AWS/EC2",
                    "MetricName": "CPUUtilization",
                    "Dimensions": [
                        {"Name": "InstanceId", "Value": resource.labels.get("instance_id", resource.name)}
                    ],
                })
                alarms.append(alarm)
            # S3 bucket NumberOfObjects alarm
            elif resource.type == "aws_s3_bucket":
                alarm = copy.deepcopy(alarm_defaults)
                alarm.update({
                    "AlarmName": f"{resource.labels.get('Name', resource.name)}-NumObjects",
                    "AlarmDescription": f"Object count for {resource.labels.get('Name', resource.name)} ({resource.address})",
                    "Namespace": "AWS/S3",
                    "MetricName": "NumberOfObjects",
                    "Dimensions": [
                        {"Name": "BucketName", "Value": resource.labels.get("Name", resource.name)},
                        {"Name": "StorageType", "Value": "AllStorageTypes"}
                    ],
                })
                alarms.append(alarm)
            # RDS instance CPUUtilization alarm
            elif resource.type == "aws_db_instance":
                alarm = copy.deepcopy(alarm_defaults)
                alarm.update({
                    "AlarmName": f"{resource.labels.get('Name', resource.name)}-RDS-HighCPU",
                    "AlarmDescription": f"High CPU for RDS {resource.labels.get('Name', resource.name)} ({resource.address})",
                    "Namespace": "AWS/RDS",
                    "MetricName": "CPUUtilization",
                    "Dimensions": [
                        {"Name": "DBInstanceIdentifier", "Value": resource.labels.get("Name", resource.name)}
                    ],
                })
                alarms.append(alarm)
            # DynamoDB table ConsumedReadCapacityUnits alarm
            elif resource.type == "aws_dynamodb_table":
                alarm = copy.deepcopy(alarm_defaults)
                alarm.update({
                    "AlarmName": f"{resource.labels.get('Name', resource.name)}-DDB-ReadCapacity",
                    "AlarmDescription": f"High read capacity for DynamoDB {resource.labels.get('Name', resource.name)} ({resource.address})",
                    "Namespace": "AWS/DynamoDB",
                    "MetricName": "ConsumedReadCapacityUnits",
                    "Dimensions": [
                        {"Name": "TableName", "Value": resource.labels.get("Name", resource.name)}
                    ],
                })
                alarms.append(alarm)
            # Lambda function Errors alarm
            elif resource.type == "aws_lambda_function":
                alarm = copy.deepcopy(alarm_defaults)
                alarm.update({
                    "AlarmName": f"{resource.labels.get('Name', resource.name)}-Lambda-Errors",
                    "AlarmDescription": f"Lambda errors for {resource.labels.get('Name', resource.name)} ({resource.address})",
                    "Namespace": "AWS/Lambda",
                    "MetricName": "Errors",
                    "Dimensions": [
                        {"Name": "FunctionName", "Value": resource.labels.get("Name", resource.name)}
                    ],
                })
                alarms.append(alarm)
            # ELB Classic HealthyHostCount alarm
            elif resource.type == "aws_elb":
                alarm = copy.deepcopy(alarm_defaults)
                alarm.update({
                    "AlarmName": f"{resource.labels.get('Name', resource.name)}-ELB-HealthyHostCount",
                    "AlarmDescription": f"ELB healthy hosts for {resource.labels.get('Name', resource.name)} ({resource.address})",
                    "Namespace": "AWS/ELB",
                    "MetricName": "HealthyHostCount",
                    "Dimensions": [
                        {"Name": "LoadBalancerName", "Value": resource.labels.get("Name", resource.name)}
                    ],
                })
                alarms.append(alarm)
            # ALB/NLB TargetGroup HealthyHostCount alarm
            elif resource.type == "aws_lb":
                alarm = copy.deepcopy(alarm_defaults)
                alarm.update({
                    "AlarmName": f"{resource.labels.get('Name', resource.name)}-LB-HealthyHostCount",
                    "AlarmDescription": f"LB healthy hosts for {resource.labels.get('Name', resource.name)} ({resource.address})",
                    "Namespace": "AWS/ApplicationELB",
                    "MetricName": "HealthyHostCount",
                    "Dimensions": [
                        {"Name": "LoadBalancer", "Value": resource.labels.get("Name", resource.name)}
                    ],
                })
                alarms.append(alarm)
            # Auto Scaling Group InServiceInstances alarm
            elif resource.type == "aws_autoscaling_group":
                alarm = copy.deepcopy(alarm_defaults)
                alarm.update({
                    "AlarmName": f"{resource.labels.get('Name', resource.name)}-ASG-InService",
                    "AlarmDescription": f"ASG in-service instances for {resource.labels.get('Name', resource.name)} ({resource.address})",
                    "Namespace": "AWS/AutoScaling",
                    "MetricName": "GroupInServiceInstances",
                    "Dimensions": [
                        {"Name": "AutoScalingGroupName", "Value": resource.labels.get("Name", resource.name)}
                    ],
                })
                alarms.append(alarm)
            # SNS Topic NumberOfMessagesPublished alarm
            elif resource.type == "aws_sns_topic":
                alarm = copy.deepcopy(alarm_defaults)
                alarm.update({
                    "AlarmName": f"{resource.labels.get('Name', resource.name)}-SNS-MessagesPublished",
                    "AlarmDescription": f"SNS messages published for {resource.labels.get('Name', resource.name)} ({resource.address})",
                    "Namespace": "AWS/SNS",
                    "MetricName": "NumberOfMessagesPublished",
                    "Dimensions": [
                        {"Name": "TopicName", "Value": resource.labels.get("Name", resource.name)}
                    ],
                })
                alarms.append(alarm)
                # Also emit alarm for NumberOfNotificationsFailed
                alarm2 = copy.deepcopy(alarm_defaults)
                alarm2.update({
                    "AlarmName": f"{resource.labels.get('Name', resource.name)}-SNS-NotificationsFailed",
                    "AlarmDescription": f"SNS notifications failed for {resource.labels.get('Name', resource.name)} ({resource.address})",
                    "Namespace": "AWS/SNS",
                    "MetricName": "NumberOfNotificationsFailed",
                    "Dimensions": [
                        {"Name": "TopicName", "Value": resource.labels.get("Name", resource.name)}
                    ],
                })
                alarms.append(alarm2)
            # SQS Queue ApproximateNumberOfMessagesVisible alarm
            elif resource.type == "aws_sqs_queue":
                alarm = copy.deepcopy(alarm_defaults)
                alarm.update({
                    "AlarmName": f"{resource.labels.get('Name', resource.name)}-SQS-MessagesVisible",
                    "AlarmDescription": f"SQS messages visible for {resource.labels.get('Name', resource.name)} ({resource.address})",
                    "Namespace": "AWS/SQS",
                    "MetricName": "ApproximateNumberOfMessagesVisible",
                    "Dimensions": [
                        {"Name": "QueueName", "Value": resource.labels.get("Name", resource.name)}
                    ],
                })
                alarms.append(alarm)
                # Also emit alarm for NumberOfMessagesReceived
                alarm2 = copy.deepcopy(alarm_defaults)
                alarm2.update({
                    "AlarmName": f"{resource.labels.get('Name', resource.name)}-SQS-MessagesReceived",
                    "AlarmDescription": f"SQS messages received for {resource.labels.get('Name', resource.name)} ({resource.address})",
                    "Namespace": "AWS/SQS",
                    "MetricName": "NumberOfMessagesReceived",
                    "Dimensions": [
                        {"Name": "QueueName", "Value": resource.labels.get("Name", resource.name)}
                    ],
                })
                alarms.append(alarm2)
        return alarms

    def run(self) -> TerraformObservabilityPackResult:
        """Execute the main operation.

        Returns:
            TerraformObservabilityPackResult with the operation outcome.
        """
        # Placeholder for main run logic
        return TerraformObservabilityPackResult(
            success=True,
            data={"message": "TerraformObservabilityPack is working!"},
        )
