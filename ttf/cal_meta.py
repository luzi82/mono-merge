#!/usr/bin/env python3
"""
Calculate font metadata from a character CSV file.
Outputs metrics including advance widths, y-bounds, character height, font height, and ascender/descender.
"""

import argparse
import csv
import sys
import yaml


def calculate_metadata(input_csv):
    """
    Calculate font metadata from a CSV file created by dump_char_csv.py.
    
    Args:
        input_csv: Path to input CSV file
        
    Returns:
        Dictionary containing calculated metadata
    """
    half_widths = []
    full_widths = []
    ymin_values = []
    ymax_values = []
    
    with open(input_csv, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            # Skip empty glyphs
            if row.get('is_empty_glyph', 'False') == 'True':
                continue
            
            # Collect advance widths
            advance_width = int(row['advance_width'])
            is_full_width = row.get('is_full_width', 'False') == 'True'
            
            if is_full_width:
                full_widths.append(advance_width)
            else:
                half_widths.append(advance_width)
            
            # Collect y bounds
            ymin = int(row['yMin'])
            ymax = int(row['yMax'])
            ymin_values.append(ymin)
            ymax_values.append(ymax)
    
    if not half_widths:
        print("Error: No half-width characters found in CSV", file=sys.stderr)
        sys.exit(1)
    
    if not ymin_values or not ymax_values:
        print("Error: No valid glyphs with bounds found in CSV", file=sys.stderr)
        sys.exit(1)
    
    # Calculate half_advance_width (most common half-width value)
    half_advance_width = max(set(half_widths), key=half_widths.count)
    
    # Calculate full_advance_width (should be half_advance_width * 2)
    full_advance_width = half_advance_width * 2
    
    # Calculate y bounds
    min_yMin = min(ymin_values)
    max_yMax = max(ymax_values)
    
    # Calculate character height
    char_height = max_yMax - min_yMin
    
    # Calculate font height (1.2 times character height)
    font_height = char_height * 1.2
    
    # Calculate ascender and descender
    # Ascender extends 60%, descender extends 40%
    # The ascender should extend above max_yMax, and descender should extend below min_yMin
    # Total extension = font_height - char_height
    extension = font_height - char_height
    ascender_extension = extension * 0.6
    descender_extension = extension * 0.4
    
    ascender = max_yMax + ascender_extension
    descender = min_yMin - descender_extension
    
    # Round to integers
    metadata = {
        'half_advance_width': int(half_advance_width),
        'full_advance_width': int(full_advance_width),
        'min_yMin': int(min_yMin),
        'max_yMax': int(max_yMax),
        'char_height': int(char_height),
        'font_height': float(font_height),
        'ascender': round(ascender),
        'descender': round(descender)
    }
    
    return metadata


def main():
    parser = argparse.ArgumentParser(
        description='Calculate font metadata from a character CSV file.'
    )
    parser.add_argument(
        'input_font_csv',
        help='Input CSV file created by dump_char_csv.py (e.g., output/Inconsolata-Regular.ascii.csv)'
    )
    parser.add_argument(
        'output_yaml',
        help='Output YAML file to write the calculated metadata'
    )
    
    args = parser.parse_args()
    
    # Calculate metadata
    metadata = calculate_metadata(args.input_font_csv)
    
    # Write to YAML file
    with open(args.output_yaml, 'w', encoding='utf-8') as f:
        yaml.dump(metadata, f, default_flow_style=False, sort_keys=False)
    
    # Print summary
    print(f"Calculated metadata:")
    print(f"  half_advance_width: {metadata['half_advance_width']}")
    print(f"  full_advance_width: {metadata['full_advance_width']}")
    print(f"  min_yMin: {metadata['min_yMin']}")
    print(f"  max_yMax: {metadata['max_yMax']}")
    print(f"  char_height: {metadata['char_height']}")
    print(f"  font_height: {metadata['font_height']}")
    print(f"  ascender: {metadata['ascender']}")
    print(f"  descender: {metadata['descender']}")
    print(f"\nOutput written to: {args.output_yaml}")


if __name__ == '__main__':
    main()
