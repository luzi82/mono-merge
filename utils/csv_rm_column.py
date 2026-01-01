#!/usr/bin/env python3

import argparse
import csv


def main():
    parser = argparse.ArgumentParser(
        description='Remove specified columns from a CSV file'
    )
    parser.add_argument(
        'input_csv',
        help='Input CSV file'
    )
    parser.add_argument(
        'rm_column_list',
        help='List of columns to be removed, separated by comma'
    )
    parser.add_argument(
        'output_csv',
        help='Output CSV file'
    )
    
    args = parser.parse_args()
    
    # Parse the column list
    columns_to_remove = [col.strip() for col in args.rm_column_list.split(',')]
    
    # Read input CSV and write output CSV
    with open(args.input_csv, 'r', newline='', encoding='utf-8') as infile:
        reader = csv.DictReader(infile)
        
        # Get fieldnames and filter out columns to remove
        original_fieldnames = reader.fieldnames
        if original_fieldnames is None:
            raise ValueError("Input CSV has no header row")
        
        # Keep only columns that are not in the remove list
        output_fieldnames = [
            field for field in original_fieldnames 
            if field not in columns_to_remove
        ]
        
        # Write output CSV
        with open(args.output_csv, 'w', newline='', encoding='utf-8') as outfile:
            writer = csv.DictWriter(outfile, fieldnames=output_fieldnames)
            writer.writeheader()
            
            # Write rows with only the remaining columns
            for row in reader:
                filtered_row = {
                    key: value for key, value in row.items() 
                    if key in output_fieldnames
                }
                writer.writerow(filtered_row)


if __name__ == '__main__':
    main()
