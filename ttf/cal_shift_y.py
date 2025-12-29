#!/usr/bin/env python3
"""
Calculate the y-shift value needed to align the mid-y of a shift CSV to match a base CSV.
"""

import argparse
import csv
import math
import yaml


def calculate_mid_y(csv_file):
    """
    Calculate the alignment y value from a CSV file.
    Alignment y is at the lower 40% position of the font's y range.
    
    Args:
        csv_file: Path to the CSV file
        
    Returns:
        The alignment y value as a float
    """
    ymin_values = []
    ymax_values = []
    
    with open(csv_file, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            # Skip empty glyphs
            if row.get('is_empty_glyph', 'False') == 'True':
                continue
            
            ymin = float(row['yMin'])
            ymax = float(row['yMax'])
            ymin_values.append(ymin)
            ymax_values.append(ymax)
    
    if not ymin_values or not ymax_values:
        raise ValueError(f"No valid glyphs found in {csv_file}")
    
    # Calculate the alignment y at the lower 40% position
    overall_ymin = min(ymin_values)
    overall_ymax = max(ymax_values)
    mid_y = overall_ymin + 0.4 * (overall_ymax - overall_ymin)
    
    return mid_y


def calculate_shift_y(base_csv, shift_csv):
    """
    Calculate the y-shift needed for shift_csv to match base_csv's alignment y (lower 40% position).
    
    Args:
        base_csv: Path to the base CSV file
        shift_csv: Path to the CSV file that needs shifting
        
    Returns:
        The shift_y value (integer, truncated towards zero)
    """
    base_mid_y = calculate_mid_y(base_csv)
    shift_mid_y = calculate_mid_y(shift_csv)
    
    # Calculate the shift needed
    shift_y = base_mid_y - shift_mid_y
    
    # Round to nearest integer, but if exactly at x.5, round towards zero
    fractional_part = abs(shift_y - math.trunc(shift_y))
    if fractional_part == 0.5:
        shift_y_int = math.trunc(shift_y)
    else:
        shift_y_int = round(shift_y)
    
    return shift_y_int


def main():
    parser = argparse.ArgumentParser(
        description='Calculate the y-shift value to align two fonts at their lower 40% y position.'
    )
    parser.add_argument(
        'input_base_csv',
        help='Input CSV file for the base font (e.g., output/Inconsolata-Regular.ascii.extremey.csv)'
    )
    parser.add_argument(
        'input_shift_csv',
        help='Input CSV file for the font to shift (e.g., output/NotoSansMonoCJKhk-VF.cjk.extremey.csv)'
    )
    parser.add_argument(
        'output_yaml',
        help='Output YAML file to write the shift_y value'
    )
    
    args = parser.parse_args()
    
    # Calculate the shift value
    shift_y = calculate_shift_y(args.input_base_csv, args.input_shift_csv)
    
    # Prepare output data
    output_data = {
        'shift_y': shift_y
    }
    
    # Write to YAML file
    with open(args.output_yaml, 'w', encoding='utf-8') as f:
        yaml.dump(output_data, f, default_flow_style=False)
    
    print(f"Calculated shift_y: {shift_y}")
    print(f"Output written to: {args.output_yaml}")


if __name__ == '__main__':
    main()
