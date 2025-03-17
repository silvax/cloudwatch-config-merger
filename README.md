# CloudWatch Config Merger

A comprehensive tool for merging two Amazon CloudWatch agent configuration files, resolving duplicates, and ensuring all unique metrics are preserved while maintaining CloudWatch agent compatibility.

## Overview

The CloudWatch Config Merger helps you combine multiple CloudWatch agent configuration files into a single unified configuration. This is particularly useful when:

- You need to combine configurations from different teams or environments
- You're updating an existing configuration with new metrics
- You want to standardize monitoring across multiple instances
- You're migrating from one monitoring setup to another

The tool handles duplicate metrics and ensures the resulting configuration follows CloudWatch agent requirements, such as maintaining a single namespace.

## Features

- Merges metrics from two CloudWatch agent configuration files
- Resolves duplicate metrics to avoid redundancy
- Preserves unique metrics from both source files
- Handles special configuration sections like `append_dimensions` and `aggregation_dimensions`
- Preserves logs configuration sections
- Can be run as a standalone script or via AWS Systems Manager Run Command
- Provides detailed warnings for potential conflicts

## How It Works

The script performs the following operations:

1. **Load Configuration Files**: Reads and parses the two JSON configuration files
2. **Merge Base Configuration**: Uses the first configuration as the base
3. **Handle Namespace**: Ensures a single namespace (uses the first config's namespace if they differ)
4. **Merge Metrics Collection**: 
   - Combines metrics_collected sections
   - Preserves unique metrics from both configurations
   - Handles different metric types (dictionary-style vs list-style)
5. **Merge Dimensions**: Combines append_dimensions and aggregation_dimensions
6. **Merge Other Sections**: Preserves logs and other configuration sections
7. **Output**: Writes the merged configuration to the specified output file

## Usage

### As a standalone script

```bash
python3 merge_cloudwatch_configs.py config1.json config2.json output.json
```

Arguments:
- `config1.json`: Path to the first CloudWatch agent configuration file
- `config2.json`: Path to the second CloudWatch agent configuration file
- `output.json`: Path where the merged configuration will be saved

### Via AWS Systems Manager Run Command

The included SSM document automates the process of merging configurations across your fleet:

1. Import the `ssm-cloudwatch-config-merger.json` document into your AWS Systems Manager Documents:
   ```bash
   aws ssm create-document \
     --name "CloudWatchConfigMerger" \
     --content file://ssm-cloudwatch-config-merger.json \
     --document-type "Command"
   ```

2. Run the document with the following parameters:
   - `config1Path`: Path to the first configuration file on the target instance
   - `config2Path`: Path to the second configuration file on the target instance
   - `outputPath`: Path where the merged configuration should be saved
   - `restartAgent`: Whether to restart the CloudWatch agent after merging (yes/no)

   ```bash
   aws ssm send-command \
     --document-name "CloudWatchConfigMerger" \
     --targets "Key=instanceids,Values=i-1234567890abcdef0" \
     --parameters '{"config1Path":["/opt/aws/amazon-cloudwatch-agent/etc/amazon-cloudwatch-agent.json"],"config2Path":["/tmp/new-cloudwatch-config.json"],"outputPath":["/opt/aws/amazon-cloudwatch-agent/etc/amazon-cloudwatch-agent-merged.json"],"restartAgent":["yes"]}'
   ```

## Installation

1. Clone this repository:
   ```bash
   git clone https://github.com/YOUR_GITHUB_USERNAME/cloudwatch-config-merger.git
   ```

2. Make the script executable:
   ```bash
   chmod +x merge_cloudwatch_configs.py
   ```

3. Before using the SSM document, update the GitHub repository information in the `sourceInfo` parameter with your actual GitHub username:
   ```json
   "sourceInfo": "{\"owner\":\"YOUR_GITHUB_USERNAME\", \"repository\":\"cloudwatch-config-merger\", \"path\":\"merge_cloudwatch_configs.py\", \"getOptions\":\"branch:main\"}"
   ```

## Testing

### Local Testing

1. Use the provided sample configurations:
   ```bash
   python3 merge_cloudwatch_configs.py sample-configs/config1.json sample-configs/config2.json test-output.json
   ```

2. Verify the output matches expectations:
   ```bash
   diff sample-configs/merged-config.json test-output.json
   ```

3. Test with your own configurations:
   ```bash
   python3 merge_cloudwatch_configs.py your-config1.json your-config2.json your-output.json
   ```

4. Validate the merged configuration with the CloudWatch agent:
   ```bash
   /opt/aws/amazon-cloudwatch-agent/bin/amazon-cloudwatch-agent-ctl -a verify -c file:your-output.json
   ```

### Testing the SSM Document

1. Create a test EC2 instance with the SSM agent and CloudWatch agent installed

2. Create two different CloudWatch agent configuration files on the instance:
   - `/opt/aws/amazon-cloudwatch-agent/etc/amazon-cloudwatch-agent.json` (existing config)
   - `/tmp/new-cloudwatch-config.json` (new config to merge)

3. Run the SSM document against the test instance:
   ```bash
   aws ssm send-command \
     --document-name "CloudWatchConfigMerger" \
     --targets "Key=instanceids,Values=i-yourinstanceid" \
     --parameters '{"config1Path":["/opt/aws/amazon-cloudwatch-agent/etc/amazon-cloudwatch-agent.json"],"config2Path":["/tmp/new-cloudwatch-config.json"],"outputPath":["/opt/aws/amazon-cloudwatch-agent/etc/amazon-cloudwatch-agent-merged.json"],"restartAgent":["yes"]}'
   ```

4. Verify the CloudWatch agent is running with the merged configuration:
   ```bash
   /opt/aws/amazon-cloudwatch-agent/bin/amazon-cloudwatch-agent-ctl -a status
   ```

5. Check CloudWatch metrics in the AWS Console to confirm the metrics from both configurations are being collected

## Common Scenarios and Examples

### Scenario 1: Combining Standard and Custom Metrics

- `config1.json`: Standard metrics (CPU, memory, disk)
- `config2.json`: Custom application metrics
- Result: A single configuration with both standard and custom metrics

### Scenario 2: Updating Metric Collection Intervals

- `config1.json`: Base configuration with 60-second intervals
- `config2.json`: Same metrics but with 30-second intervals
- Result: The merged configuration will use the collection intervals from the first config

### Scenario 3: Adding New Resources to Monitor

- `config1.json`: Monitoring root (/) and /tmp filesystems
- `config2.json`: Monitoring root (/) and /var filesystems
- Result: The merged configuration will monitor all three filesystems (/, /tmp, /var)

## Troubleshooting

- **JSON Parse Error**: Ensure both input files are valid JSON
- **Namespace Conflict**: If different namespaces are detected, the script will use the namespace from the first configuration and log a warning
- **Agent Restart Failure**: If the agent fails to restart, check the CloudWatch agent logs at `/opt/aws/amazon-cloudwatch-agent/logs/amazon-cloudwatch-agent.log`
- **Missing Metrics**: Verify the merged configuration contains all expected metrics using `cat output.json`

## Requirements

- Python 3.6 or higher
- For the SSM document: 
  - AWS Systems Manager Agent installed on target instances
  - CloudWatch agent installed on target instances
  - Appropriate IAM permissions for SSM and CloudWatch

## Notes

- When merging configurations with different namespaces, the namespace from the first configuration will be used
- The script will log warnings for any conflicts or issues encountered during the merge process
- The script preserves the agent configuration section from the first config file

## License

This project is licensed under the MIT License - see the LICENSE file for details.