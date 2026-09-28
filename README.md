# AWS CostGuard

Serverless AWS Cloud Cost Optimization and Resource Hygiene Automation.

AWS CostGuard is a Python-based FinOps automation solution designed
to identify potentially wasteful AWS resources, analyze historical
EC2 CPU utilization, enforce governance tagging, and deliver
optimization notifications through Slack.

## Technology Stack

- Amazon Web Services
- AWS Lambda (Python 3.11)
- Amazon EventBridge
- Amazon CloudWatch
- Amazon EC2
- Boto3
- Slack Incoming Webhooks
- Git and GitHub

## Core Features

- Idle EC2 instance detection
- Unattached EBS volume discovery
- Unassociated Elastic IP detection
- Historical CPU utilization analysis
- Automated governance tagging
- Estimated monthly waste reporting
- Slack notifications
- Scheduled serverless execution
- Structured logging and automated tests

## Deployment Region

Asia Pacific (Mumbai): ap-south-1

## Safety

The scanner uses read-only discovery by default.
Resource deletion is not performed automatically.

## Project Status

Development in progress.
