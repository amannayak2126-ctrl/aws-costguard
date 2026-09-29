import json
import logging
import os
import urllib.request
from urllib.error import HTTPError, URLError

from aws_costguard.scanner import CostGuardScanner

logger = logging.getLogger()
logger.setLevel(logging.INFO)


def send_slack_notification(report):
    webhook_url = os.environ.get("SLACK_WEBHOOK_URL")

    if not webhook_url:
        logger.warning("SLACK_WEBHOOK_URL is not configured; skipping Slack notification")
        return

    summary = report.get("summary", {})

    message = (
        "*AWS CostGuard scan completed*\n"
        f"Region: `{report.get('region', 'unknown')}`\n"
        f"Mode: `{report.get('mode', 'unknown')}`\n"
        f"EC2 instances discovered: {summary.get('ec2_instances_discovered', 0)}\n"
        f"Running instances: {summary.get('running_instances', 0)}\n"
        f"Unattached EBS volumes: {summary.get('unattached_ebs_volumes', 0)}\n"
        f"Unassociated Elastic IPs: {summary.get('unassociated_elastic_ips', 0)}\n"
        "\nNo AWS resources were modified."
    )

    payload = json.dumps({"text": message}).encode("utf-8")
    request = urllib.request.Request(
        webhook_url,
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    try:
        with urllib.request.urlopen(request, timeout=10) as response:
            if response.status != 200:
                raise RuntimeError(
                    f"Slack webhook returned HTTP status {response.status}"
                )
        logger.info("Slack notification sent successfully")
    except (HTTPError, URLError, TimeoutError) as exc:
        logger.exception("Slack notification failed")
        raise RuntimeError("Slack notification failed") from exc


def handler(event, context):
    logger.info("AWS CostGuard Lambda invocation started")

    scanner = CostGuardScanner()
    report = scanner.scan()

    send_slack_notification(report)

    logger.info("AWS CostGuard Lambda invocation completed")
    return report
