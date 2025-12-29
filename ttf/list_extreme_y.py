#!/usr/bin/env python3
"""
Find characters with extreme yMax and yMin values in a font character CSV.
Outputs top 5 characters with highest yMax and lowest yMin to a filtered CSV.
"""
import argparse
import csv
import sys


def find_extreme_y(input_csv, output_csv):
    """
    Find top 5 characters with highest yMax and lowest yMin.
    
    Args:
        input_csv: Path to input CSV file (from dump_char_csv.py)
        output_csv: Path to output CSV file with extreme_type column
    """
    # Read all rows from input CSV
    rows = []
    with open(input_csv, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            # Skip rows with empty yMax or yMin (empty glyphs)
            if row['yMax'] and row['yMin'] and row['advance_width']:
                try:
                    row['yMax'] = int(row['yMax'])
                    row['yMin'] = int(row['yMin'])
                    row['advance_width'] = int(row['advance_width'])
                    # Skip characters with advance_width=0
                    if row['advance_width'] == 0:
                        continue
                    rows.append(row)
                except ValueError:
                    # Skip rows with invalid numeric values
                    continue
    
    if not rows:
        print("Error: No valid rows with yMax and yMin found", file=sys.stderr)
        sys.exit(1)
    
    # Sort for yMax (descending) and get top 5
    ymax_sorted = sorted(rows, key=lambda x: x['yMax'], reverse=True)
    top_ymax = ymax_sorted[:5]
    
    # Sort for yMin (ascending) and get top 5
    ymin_sorted = sorted(rows, key=lambda x: x['yMin'])
    top_ymin = ymin_sorted[:5]
    
    # Print to stdout
    print("Top 5 characters with highest yMax:")
    for row in top_ymax:
        codepoint = row['codepoint']
        codepoint_dec = int(row['codepoint_dec'])
        ymax = row['yMax']
        char = chr(codepoint_dec) if codepoint_dec >= 32 else '<control>'
        print(f"  {codepoint} ({char}): yMax={ymax}")
    
    print("\nTop 5 characters with lowest yMin:")
    for row in top_ymin:
        codepoint = row['codepoint']
        codepoint_dec = int(row['codepoint_dec'])
        ymin = row['yMin']
        char = chr(codepoint_dec) if codepoint_dec >= 32 else '<control>'
        print(f"  {codepoint} ({char}): yMin={ymin}")
    
    # Prepare output rows with extreme_type column
    output_rows = []
    for row in top_ymax:
        row['extreme_type'] = 'yMax'
        output_rows.append(row)
    
    for row in top_ymin:
        row['extreme_type'] = 'yMin'
        output_rows.append(row)
    
    # Write to output CSV
    if output_rows:
        # Get fieldnames from first row and add extreme_type
        fieldnames = list(output_rows[0].keys())
        # Ensure extreme_type is at the end if not already there
        if 'extreme_type' in fieldnames:
            fieldnames.remove('extreme_type')
        fieldnames.append('extreme_type')
        
        with open(output_csv, 'w', encoding='utf-8', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(output_rows)
        
        print(f"\nOutput written to: {output_csv}")


def main():
    parser = argparse.ArgumentParser(
        description='Find characters with extreme yMax and yMin values in font CSV'
    )
    parser.add_argument(
        'input_csv',
        help='Input CSV file (from dump_char_csv.py)'
    )
    parser.add_argument(
        'output_csv',
        help='Output CSV file with extreme_type column'
    )
    
    args = parser.parse_args()
    
    find_extreme_y(args.input_csv, args.output_csv)


if __name__ == '__main__':
    main()
