import logging

from aws_costguard.scanner import CostGuardScanner

logger = logging.getLogger()
logger.setLevel(logging.INFO)


def handler(event, context):
    """AWS Lambda entry point for the read-only CostGuard scan."""
    logger.info("AWS CostGuard Lambda invocation started")

    scanner = CostGuardScanner()
    report = scanner.scan()

    logger.info("AWS CostGuard Lambda invocation completed")
    return report
