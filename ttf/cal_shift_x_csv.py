#!/usr/bin/env python3

import argparse
import csv
import math


def main():
    parser = argparse.ArgumentParser(
        description='Calculate x-shift and new advance width for characters'
    )
    parser.add_argument('input_csv', help='Input CSV file from dump_char_csv.py')
    parser.add_argument('advance_width', type=int, help='Target advance width for half-width characters')
    parser.add_argument('output_csv', help='Output CSV file with shift_x and new_advance_width columns')
    
    args = parser.parse_args()
    
    # Read input CSV and process
    with open(args.input_csv, 'r', encoding='utf-8') as infile, \
         open(args.output_csv, 'w', encoding='utf-8', newline='') as outfile:
        
        reader = csv.DictReader(infile)
        
        # Add new columns to fieldnames
        fieldnames = reader.fieldnames + ['shift_x', 'new_advance_width']
        writer = csv.DictWriter(outfile, fieldnames=fieldnames)
        writer.writeheader()
        
        for row in reader:
            old_advance_width = int(row['advance_width'])
            is_full_width = row['is_full_width'].lower() == 'true'
            
            # Calculate new advance width
            if is_full_width:
                new_advance_width = args.advance_width * 2
            else:
                new_advance_width = args.advance_width
            
            # Calculate x-shift
            shift_x = (new_advance_width - old_advance_width) / 2
            
            # Round shift_x: if fractional part >= 0.5, round down; otherwise round up
            frac_part = abs(shift_x) - math.floor(abs(shift_x))
            if frac_part >= 0.5:
                shift_x = math.floor(shift_x)
            else:
                shift_x = math.ceil(shift_x)
            
            # Add calculated values to row
            row['shift_x'] = shift_x
            row['new_advance_width'] = new_advance_width
            
            writer.writerow(row)


if __name__ == '__main__':
    main()
