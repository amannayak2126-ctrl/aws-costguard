import json
import logging
import os
from urllib.request import Request, urlopen

from aws_costguard.scanner import CostGuardScanner

logger = logging.getLogger()
logger.setLevel(logging.INFO)


def send_slack_notification(report, webhook_url):
    summary = report.get("summary", {})

    message = (
        "*AWS CostGuard scan completed*\n"
        f"Region: {report.get('region', 'unknown')}\n"
        f"Mode: {report.get('mode', 'unknown')}\n"
        f"EC2 instances: {summary.get('ec2_instances_discovered', 'n/a')}\n"
        f"Potentially idle instances: {summary.get('potential_idle_instances', 'n/a')}\n"
        f"Unattached EBS volumes: {summary.get('unattached_ebs_volumes', 'n/a')}\n"
        f"Unassociated Elastic IPs: {summary.get('unassociated_elastic_ips', 'n/a')}"
    )

    payload = json.dumps({"text": message}).encode("utf-8")
    request = Request(
        webhook_url,
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    with urlopen(request, timeout=10) as response:
        if response.status < 200 or response.status >= 300:
            raise RuntimeError(f"Slack notification failed with HTTP {response.status}")


def handler(event, context):
    logger.info("AWS CostGuard Lambda invocation started")

    scanner = CostGuardScanner()
    report = scanner.scan()

    webhook_url = os.environ.get("SLACK_WEBHOOK_URL")
    if webhook_url:
        send_slack_notification(report, webhook_url)
        logger.info("AWS CostGuard Slack notification sent")
    else:
        logger.warning("SLACK_WEBHOOK_URL is not configured; notification skipped")

    logger.info("AWS CostGuard Lambda invocation completed")
    return report
