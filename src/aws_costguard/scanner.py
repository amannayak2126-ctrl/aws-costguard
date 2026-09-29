
import json
import logging
from datetime import datetime, timedelta, timezone
from typing import Any

import boto3
from botocore.exceptions import BotoCoreError, ClientError


logger = logging.getLogger(__name__)

DEFAULT_REGION = "ap-south-1"
DEFAULT_CPU_THRESHOLD = 5.0
DEFAULT_LOOKBACK_DAYS = 7


class CostGuardScanner:
    """Read-only AWS resource discovery and cost optimization scanner."""

    def __init__(
        self,
        region: str = DEFAULT_REGION,
        cpu_threshold: float = DEFAULT_CPU_THRESHOLD,
        lookback_days: int = DEFAULT_LOOKBACK_DAYS,
        session: Any = None,
    ):
        self.region = region
        self.cpu_threshold = cpu_threshold
        self.lookback_days = lookback_days

        self.session = session or boto3.Session(region_name=region)
        self.ec2 = self.session.client("ec2", region_name=region)
        self.cloudwatch = self.session.client(
            "cloudwatch", region_name=region
        )

    def discover_instances(self) -> list[dict]:
        """Discover EC2 instances without modifying them."""

        instances = []
        paginator = self.ec2.get_paginator("describe_instances")

        for page in paginator.paginate():
            for reservation in page.get("Reservations", []):
                for instance in reservation.get("Instances", []):
                    instances.append({
                        "instance_id": instance["InstanceId"],
                        "instance_type": instance.get("InstanceType"),
                        "state": instance.get("State", {}).get("Name"),
                        "launch_time": (
                            instance.get("LaunchTime").isoformat()
                            if instance.get("LaunchTime")
                            else None
                        ),
                        "tags": {
                            tag["Key"]: tag["Value"]
                            for tag in instance.get("Tags", [])
                        },
                    })

        logger.info("Discovered %d EC2 instances", len(instances))
        return instances

    def discover_unattached_volumes(self) -> list[dict]:
        """Find EBS volumes that are not attached to instances."""

        findings = []
        paginator = self.ec2.get_paginator("describe_volumes")

        for page in paginator.paginate():
            for volume in page.get("Volumes", []):
                if volume.get("State") == "available":
                    findings.append({
                        "volume_id": volume["VolumeId"],
                        "size_gb": volume.get("Size"),
                        "volume_type": volume.get("VolumeType"),
                        "availability_zone": volume.get("AvailabilityZone"),
                        "finding": "UNATTACHED_EBS_VOLUME",
                        "recommendation": (
                            "Review the volume and its snapshots before "
                            "considering deletion."
                        ),
                    })

        logger.info("Discovered %d unattached EBS volumes", len(findings))
        return findings

    def discover_unassociated_addresses(self) -> list[dict]:
        """Find Elastic IP addresses without an association."""

        response = self.ec2.describe_addresses()

        findings = []

        for address in response.get("Addresses", []):
            if not address.get("AssociationId"):
                findings.append({
                    "public_ip": address.get("PublicIp"),
                    "allocation_id": address.get("AllocationId"),
                    "finding": "UNASSOCIATED_ELASTIC_IP",
                    "recommendation": (
                        "Review whether this address is still required."
                    ),
                })

        logger.info(
            "Discovered %d unassociated Elastic IPs", len(findings)
        )
        return findings

    def get_average_cpu(
        self,
        instance_id: str,
    ) -> float | None:
        """Retrieve average CPU utilization over the configured period."""

        end_time = datetime.now(timezone.utc)
        start_time = end_time - timedelta(days=self.lookback_days)

        response = self.cloudwatch.get_metric_statistics(
            Namespace="AWS/EC2",
            MetricName="CPUUtilization",
            Dimensions=[
                {
                    "Name": "InstanceId",
                    "Value": instance_id,
                }
            ],
            StartTime=start_time,
            EndTime=end_time,
            Period=3600,
            Statistics=["Average"],
        )

        datapoints = response.get("Datapoints", [])

        if not datapoints:
            logger.warning(
                "No CPU datapoints available for %s", instance_id
            )
            return None

        average = sum(
            point["Average"] for point in datapoints
        ) / len(datapoints)

        return round(average, 2)

    def analyze_idle_instances(
        self,
        instances: list[dict],
    ) -> list[dict]:
        """Identify running instances with low observed average CPU."""

        findings = []

        for instance in instances:
            if instance["state"] != "running":
                continue

            instance_id = instance["instance_id"]
            average_cpu = self.get_average_cpu(instance_id)

            if average_cpu is None:
                continue

            if average_cpu < self.cpu_threshold:
                findings.append({
                    "instance_id": instance_id,
                    "instance_type": instance["instance_type"],
                    "average_cpu_percent": average_cpu,
                    "threshold_percent": self.cpu_threshold,
                    "lookback_days": self.lookback_days,
                    "finding": "POTENTIALLY_IDLE_EC2",
                    "recommendation": (
                        "Review workload, memory, network, and business "
                        "requirements before resizing or stopping."
                    ),
                })

        logger.info("Identified %d potentially idle instances", len(findings))
        return findings

    def scan(self) -> dict:
        """Run all read-only discovery checks."""

        logger.info("Starting AWS CostGuard scan in %s", self.region)

        instances = self.discover_instances()
        unattached_volumes = self.discover_unattached_volumes()
        unassociated_addresses = self.discover_unassociated_addresses()
        idle_instances = self.analyze_idle_instances(instances)

        report = {
            "project": "AWS CostGuard",
            "region": self.region,
            "scan_timestamp": datetime.now(timezone.utc).isoformat(),
            "mode": "READ_ONLY",
            "summary": {
                "ec2_instances_discovered": len(instances),
                "potentially_idle_instances": len(idle_instances),
                "unattached_ebs_volumes": len(unattached_volumes),
                "unassociated_elastic_ips": len(unassociated_addresses),
            },
            "findings": {
                "potentially_idle_instances": idle_instances,
                "unattached_ebs_volumes": unattached_volumes,
                "unassociated_elastic_ips": unassociated_addresses,
            },
            "cost_estimation": {
                "status": "NOT_CONFIGURED",
                "note": (
                    "No dollar savings are claimed until verified "
                    "regional pricing assumptions are configured."
                ),
            },
        }

        logger.info("AWS CostGuard scan completed")
        return report


def main():
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )

    scanner = CostGuardScanner()
    report = scanner.scan()

    print(json.dumps(report, indent=2, default=str))


if __name__ == "__main__":
    main()
