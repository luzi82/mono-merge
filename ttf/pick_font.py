#!/usr/bin/env python3
"""
Pick font source for each character based on availability and metrics.
Merges multiple CSV files from dump_char_csv.py and determines which font to use for each codepoint.
"""
import argparse
import csv
import sys


def is_valid_glyph(row):
    """
    Check if a glyph is valid for use (has positive width and is not empty).
    
    Args:
        row: Dictionary containing CSV row data
        
    Returns:
        True if glyph is valid, False otherwise
    """
    try:
        advance_width = int(row.get('advance_width', 0))
        is_empty = row.get('is_empty_glyph', 'True') == 'True'
        return advance_width > 0 and not is_empty
    except (ValueError, TypeError):
        return False


def pick_font_sources(input_csv_paths, output_csv):
    """
    Merge multiple character CSV files and pick font source for each character.
    
    Logic (evaluated in order):
    1. First pass: Check each CSV in order for valid glyph (advance_width > 0 AND not is_empty_glyph)
    2. Second pass: If no valid glyph found, check each CSV in order for any existing character
    
    Args:
        input_csv_paths: List of paths to input font CSV files
        output_csv: Path to output CSV file
    """
    if not input_csv_paths:
        print("Error: No input CSV files provided", file=sys.stderr)
        sys.exit(1)
    
    # Open all input files
    try:
        input_files = [open(path, 'r', encoding='utf-8', newline='') for path in input_csv_paths]
        out_file = open(output_csv, 'w', encoding='utf-8', newline='')
    except IOError as e:
        print(f"Error opening files: {e}", file=sys.stderr)
        sys.exit(1)
    
    try:
        readers = [csv.DictReader(f) for f in input_files]
        
        # Verify required columns and get field structure from first CSV
        first_fields = readers[0].fieldnames
        if not first_fields or 'codepoint_dec' not in first_fields:
            print("Error: First CSV missing required columns", file=sys.stderr)
            sys.exit(1)
        
        # Verify all CSVs have the same field structure
        for i, reader in enumerate(readers[1:], start=1):
            if reader.fieldnames != first_fields:
                print(f"Error: CSV file {i} has different field structure than first CSV", file=sys.stderr)
                print(f"First CSV fields: {first_fields}", file=sys.stderr)
                print(f"CSV {i} fields: {reader.fieldnames}", file=sys.stderr)
                sys.exit(1)
        
        # Use first CSV fields as template and add 'pick' column
        output_fields = list(first_fields)
        if 'pick' not in output_fields:
            output_fields.append('pick')
        
        writer = csv.DictWriter(out_file, fieldnames=output_fields)
        writer.writeheader()
        
        # Initialize current rows for each reader
        current_rows = [next(reader, None) for reader in readers]
        
        # Stream through all files (all sorted by codepoint_dec)
        while any(row is not None for row in current_rows):
            # Find the minimum codepoint among all current rows
            min_cp = float('inf')
            for row in current_rows:
                if row is not None:
                    cp = int(row['codepoint_dec'])
                    if cp < min_cp:
                        min_cp = cp
            
            if min_cp == float('inf'):
                break
            
            # Collect all rows with this codepoint
            rows_at_cp = []
            for i, row in enumerate(current_rows):
                if row is not None and int(row['codepoint_dec']) == min_cp:
                    rows_at_cp.append((i, row))
            
            # Apply picking logic: First pass - find valid glyph
            picked_index = None
            picked_row = None
            
            for csv_index in range(len(readers)):
                matching = [row for idx, row in rows_at_cp if idx == csv_index]
                if matching and is_valid_glyph(matching[0]):
                    picked_index = csv_index
                    picked_row = matching[0]
                    break
            
            # Second pass - find any existing character if no valid glyph found
            if picked_index is None:
                for csv_index in range(len(readers)):
                    matching = [row for idx, row in rows_at_cp if idx == csv_index]
                    if matching:
                        picked_index = csv_index
                        picked_row = matching[0]
                        break
            
            # Write output row
            if picked_row is not None:
                output_row = picked_row.copy()
                output_row['pick'] = str(picked_index)
                writer.writerow(output_row)
            
            # Advance readers that had this codepoint
            for i, row in enumerate(current_rows):
                if row is not None and int(row['codepoint_dec']) == min_cp:
                    current_rows[i] = next(readers[i], None)
    
    finally:
        for f in input_files:
            f.close()
        out_file.close()


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description='Pick font source for each character based on availability and metrics'
    )
    parser.add_argument(
        'input_csv_list',
        help='Comma-separated list of input font CSV files (from dump_char_csv.py), e.g. "font1.csv,font2.csv"'
    )
    parser.add_argument(
        'output_csv',
        help='Output CSV file with pick column'
    )
    
    args = parser.parse_args()
    
    # Parse comma-separated CSV list
    input_csv_paths = [path.strip() for path in args.input_csv_list.split(',')]
    
    pick_font_sources(input_csv_paths, args.output_csv)
    print(f"Font picking complete. Output written to: {args.output_csv}")


if __name__ == '__main__':
    main()
