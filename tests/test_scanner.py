import unittest
from unittest.mock import MagicMock

from aws_costguard.scanner import CostGuardScanner


class TestCostGuardScanner(unittest.TestCase):
    def make_scanner(self):
        """Create a scanner with mocked AWS clients."""
        scanner = CostGuardScanner.__new__(CostGuardScanner)
        scanner.region = "ap-south-1"
        scanner.cpu_threshold = 5.0
        scanner.lookback_days = 7
        scanner.ec2 = MagicMock()
        scanner.cloudwatch = MagicMock()
        return scanner

    def test_discover_instances_returns_instance_details(self):
        scanner = self.make_scanner()
        paginator = scanner.ec2.get_paginator.return_value
        paginator.paginate.return_value = [{
            "Reservations": [{
                "Instances": [{
                    "InstanceId": "i-example123",
                    "InstanceType": "t3.micro",
                    "State": {"Name": "running"},
                    "LaunchTime": None,
                    "Tags": [{"Key": "Environment", "Value": "test"}],
                }]
            }]
        }]

        instances = scanner.discover_instances()

        self.assertEqual(len(instances), 1)
        self.assertEqual(instances[0]["instance_id"], "i-example123")
        self.assertEqual(instances[0]["state"], "running")
        self.assertEqual(instances[0]["tags"]["Environment"], "test")

    def test_discover_unattached_volumes_only_returns_available(self):
        scanner = self.make_scanner()
        paginator = scanner.ec2.get_paginator.return_value
        paginator.paginate.return_value = [{
            "Volumes": [
                {
                    "VolumeId": "vol-unattached",
                    "State": "available",
                    "Size": 8,
                    "VolumeType": "gp3",
                    "AvailabilityZone": "ap-south-1a",
                },
                {
                    "VolumeId": "vol-attached",
                    "State": "in-use",
                    "Size": 8,
                    "VolumeType": "gp3",
                    "AvailabilityZone": "ap-south-1a",
                },
            ]
        }]

        findings = scanner.discover_unattached_volumes()

        self.assertEqual(len(findings), 1)
        self.assertEqual(findings[0]["volume_id"], "vol-unattached")
        self.assertEqual(findings[0]["finding"], "UNATTACHED_EBS_VOLUME")

    def test_discover_unassociated_addresses(self):
        scanner = self.make_scanner()
        scanner.ec2.describe_addresses.return_value = {
            "Addresses": [
                {
                    "PublicIp": "198.51.100.10",
                    "AllocationId": "eipalloc-example",
                },
                {
                    "PublicIp": "198.51.100.11",
                    "AllocationId": "eipalloc-associated",
                    "AssociationId": "eipassoc-example",
                },
            ]
        }

        findings = scanner.discover_unassociated_addresses()

        self.assertEqual(len(findings), 1)
        self.assertEqual(findings[0]["public_ip"], "198.51.100.10")
        self.assertEqual(findings[0]["finding"], "UNASSOCIATED_ELASTIC_IP")

    def test_get_average_cpu_calculates_mean(self):
        scanner = self.make_scanner()
        scanner.cloudwatch.get_metric_statistics.return_value = {
            "Datapoints": [
                {"Average": 2.0},
                {"Average": 4.0},
                {"Average": 6.0},
            ]
        }

        average = scanner.get_average_cpu("i-example123")

        self.assertEqual(average, 4.0)
        scanner.cloudwatch.get_metric_statistics.assert_called_once()

    def test_get_average_cpu_returns_none_without_datapoints(self):
        scanner = self.make_scanner()
        scanner.cloudwatch.get_metric_statistics.return_value = {
            "Datapoints": []
        }

        self.assertIsNone(scanner.get_average_cpu("i-example123"))

    def test_analyze_idle_instances_only_flags_low_cpu_running_instances(self):
        scanner = self.make_scanner()
        scanner.get_average_cpu = MagicMock(return_value=2.5)

        instances = [
            {
                "instance_id": "i-running",
                "instance_type": "t3.micro",
                "state": "running",
            },
            {
                "instance_id": "i-stopped",
                "instance_type": "t3.micro",
                "state": "stopped",
            },
        ]

        findings = scanner.analyze_idle_instances(instances)

        self.assertEqual(len(findings), 1)
        self.assertEqual(findings[0]["instance_id"], "i-running")
        self.assertEqual(findings[0]["finding"], "POTENTIALLY_IDLE_EC2")
        scanner.get_average_cpu.assert_called_once_with("i-running")

    def test_analyze_idle_instances_does_not_flag_cpu_at_threshold(self):
        scanner = self.make_scanner()
        scanner.get_average_cpu = MagicMock(return_value=5.0)

        instances = [{
            "instance_id": "i-at-threshold",
            "instance_type": "t3.micro",
            "state": "running",
        }]

        findings = scanner.analyze_idle_instances(instances)

        self.assertEqual(findings, [])


if __name__ == "__main__":
    unittest.main()
