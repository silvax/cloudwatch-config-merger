#!/usr/bin/env python3
"""
CloudWatch Agent Configuration Merger

This script merges two CloudWatch agent configuration files, resolving duplicates
and ensuring that the resulting configuration contains all unique metrics from both files.
"""

import json
import argparse
import os
import sys
from typing import Dict, Any, List


def load_config(file_path: str) -> Dict[str, Any]:
    """
    Load a CloudWatch agent configuration file.
    
    Args:
        file_path: Path to the configuration file
        
    Returns:
        The loaded configuration as a dictionary
    """
    try:
        with open(file_path, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"Error: File {file_path} not found.")
        sys.exit(1)
    except json.JSONDecodeError:
        print(f"Error: File {file_path} is not valid JSON.")
        sys.exit(1)


def merge_metrics(config1: Dict[str, Any], config2: Dict[str, Any]) -> Dict[str, Any]:
    """
    Merge metrics from two CloudWatch agent configurations.
    
    Args:
        config1: First configuration
        config2: Second configuration
        
    Returns:
        Merged configuration
    """
    # Start with the first config as the base
    merged_config = config1.copy()
    
    # If metrics section doesn't exist in either config, handle accordingly
    if "metrics" not in merged_config:
        if "metrics" in config2:
            merged_config["metrics"] = config2["metrics"].copy()
        return merged_config
    
    if "metrics" not in config2:
        return merged_config
    
    # Handle namespace - CloudWatch agent only supports one namespace
    # If namespaces differ, we'll keep the first one and log a warning
    if ("metrics" in config1 and "metrics" in config2 and 
        "namespace" in config1["metrics"] and "namespace" in config2["metrics"] and
        config1["metrics"]["namespace"] != config2["metrics"]["namespace"]):
        print(f"Warning: Different namespaces found. Using '{config1['metrics']['namespace']}' from first config.")
    
    # Merge metrics_collected section
    if ("metrics_collected" not in merged_config["metrics"] and 
        "metrics_collected" in config2["metrics"]):
        merged_config["metrics"]["metrics_collected"] = config2["metrics"]["metrics_collected"].copy()
    elif ("metrics_collected" in merged_config["metrics"] and 
          "metrics_collected" in config2["metrics"]):
        # For each metric type in config2
        for metric_type, metrics in config2["metrics"]["metrics_collected"].items():
            if metric_type not in merged_config["metrics"]["metrics_collected"]:
                # If metric type doesn't exist in merged config, add it
                merged_config["metrics"]["metrics_collected"][metric_type] = metrics
            else:
                # If metric type exists, merge the metrics
                if isinstance(metrics, dict):
                    # For dictionary-style metrics (like disk, cpu, etc.)
                    for key, value in metrics.items():
                        if key not in merged_config["metrics"]["metrics_collected"][metric_type]:
                            merged_config["metrics"]["metrics_collected"][metric_type][key] = value
                elif isinstance(metrics, list):
                    # For list-style metrics
                    existing_metrics = set(merged_config["metrics"]["metrics_collected"][metric_type])
                    for metric in metrics:
                        if metric not in existing_metrics:
                            merged_config["metrics"]["metrics_collected"][metric_type].append(metric)
    
    # Merge append_dimensions if present
    if "append_dimensions" in config2.get("metrics", {}):
        if "append_dimensions" not in merged_config["metrics"]:
            merged_config["metrics"]["append_dimensions"] = config2["metrics"]["append_dimensions"].copy()
        else:
            for key, value in config2["metrics"]["append_dimensions"].items():
                if key not in merged_config["metrics"]["append_dimensions"]:
                    merged_config["metrics"]["append_dimensions"][key] = value
    
    # Merge aggregation_dimensions if present
    if "aggregation_dimensions" in config2.get("metrics", {}):
        if "aggregation_dimensions" not in merged_config["metrics"]:
            merged_config["metrics"]["aggregation_dimensions"] = config2["metrics"]["aggregation_dimensions"].copy()
        else:
            # For aggregation_dimensions, we need to check for duplicates in the list of dimension lists
            existing_dims = [tuple(sorted(dim_list)) for dim_list in merged_config["metrics"]["aggregation_dimensions"]]
            for dim_list in config2["metrics"]["aggregation_dimensions"]:
                if tuple(sorted(dim_list)) not in existing_dims:
                    merged_config["metrics"]["aggregation_dimensions"].append(dim_list)
    
    # Handle other configuration sections (logs, etc.) if needed
    for section in config2:
        if section != "metrics" and section not in merged_config:
            merged_config[section] = config2[section].copy()
    
    return merged_config


def main():
    parser = argparse.ArgumentParser(description='Merge two CloudWatch agent configuration files.')
    parser.add_argument('config1', help='Path to the first configuration file')
    parser.add_argument('config2', help='Path to the second configuration file')
    parser.add_argument('output', help='Path to the output merged configuration file')
    
    args = parser.parse_args()
    
    # Load configurations
    config1 = load_config(args.config1)
    config2 = load_config(args.config2)
    
    # Merge configurations
    merged_config = merge_metrics(config1, config2)
    
    # Write merged configuration to output file
    try:
        with open(args.output, 'w') as f:
            json.dump(merged_config, f, indent=2)
        print(f"Merged configuration written to {args.output}")
    except IOError as e:
        print(f"Error writing to output file: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()