#!/usr/bin/env python3

import argparse
import csv
import sys


def main():
    parser = argparse.ArgumentParser(
        description='Set specific columns to given values in a CSV file'
    )
    parser.add_argument('input_csv', help='Input CSV file path')
    parser.add_argument(
        'key_value_pairs',
        help='Column names and values in format: key0:value0,key1:value1,...'
    )
    parser.add_argument('output_csv', help='Output CSV file path')
    
    args = parser.parse_args()
    
    # Parse key-value pairs
    column_values = {}
    try:
        pairs = args.key_value_pairs.split(',')
        for pair in pairs:
            if ':' not in pair:
                print(f"Error: Invalid format in pair '{pair}'. Expected 'key:value'", file=sys.stderr)
                sys.exit(1)
            key, value = pair.split(':', 1)
            column_values[key] = value
    except Exception as e:
        print(f"Error parsing key-value pairs: {e}", file=sys.stderr)
        sys.exit(1)
    
    # Read input CSV and write output CSV
    try:
        with open(args.input_csv, 'r', newline='', encoding='utf-8') as infile:
            reader = csv.DictReader(infile)
            fieldnames = list(reader.fieldnames) if reader.fieldnames else []
            
            if not fieldnames:
                print("Error: Input CSV has no header row", file=sys.stderr)
                sys.exit(1)
            
            # Add new columns to the end if they don't exist
            for key in column_values.keys():
                if key not in fieldnames:
                    fieldnames.append(key)
            
            with open(args.output_csv, 'w', newline='', encoding='utf-8') as outfile:
                writer = csv.DictWriter(outfile, fieldnames=fieldnames)
                writer.writeheader()
                
                for row in reader:
                    # Set the specified columns to the specified values
                    for key, value in column_values.items():
                        row[key] = value
                    writer.writerow(row)
    
    except FileNotFoundError:
        print(f"Error: File '{args.input_csv}' not found", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Error processing CSV: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()
