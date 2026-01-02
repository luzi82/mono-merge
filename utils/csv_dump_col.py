#!/usr/bin/env python3

import argparse
import csv
import sys


def main():
    parser = argparse.ArgumentParser(
        description='Dump specific columns from a CSV file to stdout'
    )
    parser.add_argument('input_csv', help='Input CSV file path')
    parser.add_argument(
        'columns',
        help='Comma-separated list of column names to dump'
    )
    parser.add_argument(
        '--header',
        action='store_true',
        help='Include header in output'
    )
    
    args = parser.parse_args()
    
    # Parse column list
    column_list = [col.strip() for col in args.columns.split(',')]
    
    if not column_list:
        print("Error: No columns specified", file=sys.stderr)
        sys.exit(1)
    
    # Read input CSV and write output CSV
    try:
        with open(args.input_csv, 'r', newline='', encoding='utf-8') as infile:
            reader = csv.DictReader(infile)
            fieldnames = reader.fieldnames
            
            if fieldnames is None:
                print("Error: Input CSV has no header row", file=sys.stderr)
                sys.exit(1)
            
            # Check if all columns exist in the CSV
            for col in column_list:
                if col not in fieldnames:
                    print(f"Error: Column '{col}' not found in CSV", file=sys.stderr)
                    sys.exit(1)
            
            # Output to stdout
            writer = csv.writer(sys.stdout)
            
            # Write header if requested
            if args.header:
                writer.writerow(column_list)
            
            # Write rows
            for row in reader:
                output_row = [row[col] for col in column_list]
                writer.writerow(output_row)
    
    except FileNotFoundError:
        print(f"Error: File '{args.input_csv}' not found", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Error processing CSV: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()
