#!/usr/bin/env python3
import argparse
import csv
import sys
import re

def main():
    parser = argparse.ArgumentParser(description="Query a value from a CSV file.")
    parser.add_argument("input_csv", help="The CSV file to query")
    parser.add_argument("search_column", help="The column to search")
    parser.add_argument("search_value", help="The value to search")
    parser.add_argument("pull_column", help="The column to pull out")

    args = parser.parse_args()

    try:
        with open(args.input_csv, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            
            # Check if file is empty or couldn't read header
            if reader.fieldnames is None:
                # This might happen if the file is completely empty
                sys.exit(1)

            if args.search_column not in reader.fieldnames:
                sys.exit(1)
            
            if args.pull_column not in reader.fieldnames:
                sys.exit(1)

            # Handle __MAX__ special case
            if args.search_value == "__MAX__":
                max_row = None
                max_value = None
                
                for row in reader:
                    try:
                        current_value = float(row[args.search_column])
                        if max_value is None or current_value > max_value:
                            max_value = current_value
                            max_row = row
                    except ValueError:
                        # Skip rows with non-numeric values
                        continue
                
                if max_row is not None:
                    print(max_row[args.pull_column])
                else:
                    sys.exit(1)
            # Handle __xx%__ percentile pattern
            elif re.match(r'^__\d+%__$', args.search_value):
                # Extract percentile value
                percentile_str = args.search_value[2:-3]  # Remove __ and %__
                percentile = int(percentile_str)
                
                if percentile < 0 or percentile > 100:
                    sys.exit(1)
                
                # Collect all numeric values with their rows
                values_with_rows = []
                for row in reader:
                    try:
                        current_value = float(row[args.search_column])
                        values_with_rows.append((current_value, row))
                    except ValueError:
                        # Skip rows with non-numeric values
                        continue
                
                if not values_with_rows:
                    sys.exit(1)
                
                # Sort by value in descending order
                values_with_rows.sort(key=lambda x: x[0], reverse=True)
                
                # Calculate the index for the percentile
                # percentile% highest means we want the value at (100-percentile)th percentile
                # For example, 95% highest means top 5% (95th percentile from bottom = 5% from top)
                index = int(len(values_with_rows) * (100 - percentile) / 100)
                if index >= len(values_with_rows):
                    index = len(values_with_rows) - 1
                
                target_row = values_with_rows[index][1]
                print(target_row[args.pull_column])
            else:
                # Original exact match logic
                found = False
                for row in reader:
                    if row[args.search_column] == args.search_value:
                        print(row[args.pull_column])
                        found = True
                        break
                
                if not found:
                    sys.exit(1)

    except Exception:
        sys.exit(1)

if __name__ == "__main__":
    main()
