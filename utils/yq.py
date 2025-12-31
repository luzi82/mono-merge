#!/usr/bin/env python3
"""
YAML Query Utility

Extract values from YAML files.
"""

import argparse
import sys
import yaml


def main():
    parser = argparse.ArgumentParser(description='Query YAML files')
    parser.add_argument('yaml_file', help='Path to YAML file')
    parser.add_argument('key', help='Key to extract from YAML')
    args = parser.parse_args()
    
    try:
        with open(args.yaml_file, 'r') as f:
            data = yaml.safe_load(f)
        
        # Navigate nested keys using dot notation
        keys = args.key.split('.')
        value = data
        for k in keys:
            if isinstance(value, dict):
                value = value.get(k)
                if value is None:
                    print(f"ERROR: Key '{k}' not found", file=sys.stderr)
                    sys.exit(1)
            else:
                print(f"ERROR: Cannot traverse key '{k}' in non-dict value", file=sys.stderr)
                sys.exit(1)
        
        # Print the value
        print(value)
    
    except FileNotFoundError:
        print(f"ERROR: File not found: {args.yaml_file}", file=sys.stderr)
        sys.exit(1)
    except yaml.YAMLError as e:
        print(f"ERROR: Failed to parse YAML: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
