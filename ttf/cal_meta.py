#!/usr/bin/env python3
"""
Calculate font metadata from a character CSV file.
Outputs metrics including advance widths, y-bounds, character height, font height, and ascender/descender.
"""

import argparse
import csv
import sys
import yaml


def calculate_metadata(input_height_csv, input_y_csv, height_multiplier=1.2):
    """
    Calculate font metadata from CSV files created by dump_char_csv.py.
    
    Args:
        input_height_csv: Path to input CSV file for determining font height
        input_y_csv: Path to input CSV file for determining font y position
        height_multiplier: Multiplier for font height calculation (default: 1.2)
        
    Returns:
        Dictionary containing calculated metadata
    """
    half_widths = []
    full_widths = []
    ymin_height_values = []
    ymax_height_values = []
    ymax_y_values = []
    
    # Read input_height_csv for advance widths and char height calculation
    with open(input_height_csv, 'r', encoding='utf-8') as f:
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
            
            # Collect y bounds for height calculation
            ymin = int(row['yMin'])
            ymax = int(row['yMax'])
            ymin_height_values.append(ymin)
            ymax_height_values.append(ymax)
    
    # Read input_y_csv for y position calculation
    with open(input_y_csv, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            # Skip empty glyphs
            if row.get('is_empty_glyph', 'False') == 'True':
                continue
            
            # Collect max y for ascender calculation
            ymax = int(row['yMax'])
            ymax_y_values.append(ymax)
    
    if not half_widths:
        print("Error: No half-width characters found in height CSV", file=sys.stderr)
        sys.exit(1)
    
    if not ymin_height_values or not ymax_height_values:
        print("Error: No valid glyphs with bounds found in height CSV", file=sys.stderr)
        sys.exit(1)
    
    if not ymax_y_values:
        print("Error: No valid glyphs with bounds found in y CSV", file=sys.stderr)
        sys.exit(1)
    
    # Calculate half_advance_width (most common half-width value)
    half_advance_width = max(set(half_widths), key=half_widths.count)
    
    # Calculate full_advance_width (should be half_advance_width * 2)
    full_advance_width = half_advance_width * 2
    
    # Calculate y bounds from height CSV
    min_yMin_height = min(ymin_height_values)
    max_yMax_height = max(ymax_height_values)
    
    # Calculate character height from height CSV
    char_height = max_yMax_height - min_yMin_height
    
    # Calculate font height
    font_height = char_height * height_multiplier
    
    # Get max y from y CSV
    max_yMax_y = max(ymax_y_values)
    
    # Calculate ascender and descender
    # Ascender extends from max y in y CSV, descender extends from zero
    # Extension ratio is 1:1 (50% each)
    # Total extension needed so that (ascender - descender) = font_height
    # ascender - descender = (max_yMax_y + ext) - (0 - ext) = max_yMax_y + 2*ext = font_height
    # Therefore: 2*ext = font_height - max_yMax_y, ext = (font_height - max_yMax_y) / 2
    extension = (font_height - max_yMax_y) / 2
    ascender_extension = extension
    descender_extension = extension
    
    ascender = max_yMax_y + ascender_extension
    descender = 0 - descender_extension
    
    # Round to integers
    metadata = {
        'half_advance_width': int(half_advance_width),
        'full_advance_width': int(full_advance_width),
        'min_yMin': int(min_yMin_height),
        'max_yMax': int(max_yMax_y),
        'char_height': int(char_height),
        'font_height': float(font_height),
        'ascender': round(ascender),
        'descender': round(descender)
    }
    
    return metadata


def main():
    parser = argparse.ArgumentParser(
        description='Calculate font metadata from character CSV files.'
    )
    parser.add_argument(
        'input_height_font_csv',
        help='Input CSV file for determining font height (created by dump_char_csv.py)'
    )
    parser.add_argument(
        'input_y_font_csv',
        help='Input CSV file for determining font y position (created by dump_char_csv.py)'
    )
    parser.add_argument(
        'output_yaml',
        help='Output YAML file to write the calculated metadata'
    )
    parser.add_argument(
        '--height-multiplier',
        type=float,
        default=1.2,
        help='Multiplier for font height calculation (default: 1.2)'
    )
    
    args = parser.parse_args()
    
    # Calculate metadata
    metadata = calculate_metadata(args.input_height_font_csv, args.input_y_font_csv, args.height_multiplier)
    
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
