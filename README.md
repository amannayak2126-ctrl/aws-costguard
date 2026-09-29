# AWS CostGuard

A serverless AWS resource monitoring and cost-optimization project built using Python, Boto3, AWS Lambda, CloudWatch, and Slack.

## About the Project

I built AWS CostGuard to explore how AWS services can be used to identify potentially wasteful resources and make cloud infrastructure easier to monitor.

The project scans selected AWS resources, checks EC2 CPU utilization, and sends a summary of the scan to Slack. I deployed and tested the scanner using AWS Lambda and documented the implementation with screenshots.

The scanner is designed for **read-only resource discovery**. It does not automatically stop instances, delete resources, or modify infrastructure.

## Features

- Scan EC2 instances in a configured AWS region.
- Identify running EC2 instances with low CPU utilization.
- Discover EBS volumes and report their attachment status.
- Identify Elastic IP addresses that are not associated with an instance.
- Retrieve EC2 CPU utilization metrics from CloudWatch.
- Send scan summaries to Slack using an incoming webhook.
- Run the scanner through AWS Lambda.
- Record execution details in CloudWatch Logs.
- Run unit tests using mocked AWS interactions.

## Technology Used

- Python
- Linux (Ubuntu on WSL)
- Boto3
- AWS Lambda
- Amazon EC2
- Amazon EBS
- Amazon CloudWatch
- Slack Incoming Webhooks
- Python `unittest`
- Git and GitHub


## Development Environment

I developed and tested this project using Ubuntu Linux through WSL on Windows.

I used the Linux terminal for Python environment setup, installing dependencies, running unit tests, preparing the Lambda deployment package, and working with Git and the AWS CLI.


## How It Works

1. AWS Lambda invokes the CostGuard handler.
2. The scanner uses Boto3 to inspect EC2 instances, EBS volumes, and Elastic IP addresses.
3. It retrieves CPU utilization metrics from CloudWatch.
4. The scan results are logged and summarized.
5. If a Slack webhook is configured, the summary is sent to the designated Slack channel.

## AWS Configuration

I deployed and tested the Lambda function in the **Asia Pacific (Mumbai)** region (`ap-south-1`).

| Configuration | Value |
|---|---|
| Lambda function | `aws-costguard-scanner` |
| Runtime | Python 3.12 |
| Handler | `aws_costguard.lambda_handler.handler` |
| Memory | 128 MB |
| Timeout | 30 seconds |
| AWS Region | `ap-south-1` |

The Lambda execution role used read-only permissions for the required EC2 and CloudWatch operations:

- `ec2:DescribeInstances`
- `ec2:DescribeVolumes`
- `ec2:DescribeAddresses`
- `cloudwatch:GetMetricStatistics`

## Slack Notifications

I configured a Slack incoming webhook so the Lambda function could send scan summaries to a Slack channel.

The webhook URL is supplied through the Lambda environment variable:

```text
SLACK_WEBHOOK_URL
```

I have not included the webhook URL or any credentials in this repository.

## Running the Tests

The project includes unit tests that mock AWS interactions.

To run the tests locally:

```bash
PYTHONPATH=src python -m unittest discover -s tests -v
```

## Project Structure

```text
aws-costguard/
├── src/
│   └── aws_costguard/
│       ├── __init__.py
│       ├── scanner.py
│       └── lambda_handler.py
├── tests/
├── docs/
│   └── screenshots/
├── .gitignore
├── LICENSE
├── README.md
└── requirements.txt
```

## Screenshots and Evidence

I documented the project implementation and testing process with screenshots.

The evidence includes:

- Repository and test results
- Lambda configuration
- IAM permissions
- Slack webhook configuration
- Successful scan output
- CloudWatch logs and monitoring
- Slack notification

Screenshots are available in [`docs/screenshots/`](docs/screenshots/).

## Current Scope

This version focuses on resource discovery, CPU metric retrieval, logging, and Slack notifications.

It does not currently perform automatic resource deletion, governance tagging, monthly cost estimation, or scheduled execution through EventBridge.

Any resource identified by the scanner should be reviewed before taking action.

## Project Status

**Completed and tested.**

I successfully tested the scanner through AWS Lambda, verified the scan output and CloudWatch logs, and confirmed Slack notification delivery. I also ran the unit tests and captured screenshots of the implementation.

After completing the demo, I began cleaning up the project-specific AWS resources.

## License

This project is licensed under the MIT License. See [LICENSE](LICENSE) for details.
