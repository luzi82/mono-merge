#!/usr/bin/env python3
"""
Pick font source (base or new) for each character based on availability and metrics.
Merges two CSV files from dump_char_csv.py and determines which font to use for each codepoint.
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


def pick_font_sources(input_base_csv, input_new_csv, output_csv):
    """
    Merge two character CSV files and pick font source for each character.
    
    Logic (evaluated top to bottom):
    1. If exists in base font AND advance_width > 0 AND not is_empty_glyph → use "base"
    2. Else if exists in new font AND advance_width > 0 AND not is_empty_glyph → use "new"
    3. Else → use "base"
    
    Args:
        input_base_csv: Path to base font CSV file
        input_new_csv: Path to new font CSV file
        output_csv: Path to output CSV file
    """
    try:
        base_file = open(input_base_csv, 'r', encoding='utf-8', newline='')
        new_file = open(input_new_csv, 'r', encoding='utf-8', newline='')
        out_file = open(output_csv, 'w', encoding='utf-8', newline='')
    except IOError as e:
        print(f"Error opening files: {e}", file=sys.stderr)
        sys.exit(1)
    
    try:
        base_reader = csv.DictReader(base_file)
        new_reader = csv.DictReader(new_file)
        
        # Verify required columns
        base_fields = base_reader.fieldnames
        new_fields = new_reader.fieldnames
        
        if not base_fields or 'codepoint_dec' not in base_fields:
            print("Error: Base CSV missing required columns", file=sys.stderr)
            sys.exit(1)
        
        if not new_fields or 'codepoint_dec' not in new_fields:
            print("Error: New CSV missing required columns", file=sys.stderr)
            sys.exit(1)
        
        # Verify both CSVs have the same field structure
        if base_fields != new_fields:
            print("Error: Base and new CSV files have different field structures", file=sys.stderr)
            print(f"Base fields: {base_fields}", file=sys.stderr)
            print(f"New fields: {new_fields}", file=sys.stderr)
            sys.exit(1)
        
        # Use base font fields as template and add 'pick' column
        output_fields = list(base_fields)
        if 'pick' not in output_fields:
            output_fields.append('pick')
        
        writer = csv.DictWriter(out_file, fieldnames=output_fields)
        writer.writeheader()
        
        # Stream through both files (both sorted by codepoint_dec)
        base_row = next(base_reader, None)
        new_row = next(new_reader, None)
        
        while base_row is not None or new_row is not None:
            base_cp = int(base_row['codepoint_dec']) if base_row else float('inf')
            new_cp = int(new_row['codepoint_dec']) if new_row else float('inf')
            
            if base_cp < new_cp:
                # Character only in base font
                output_row = base_row.copy()
                if is_valid_glyph(base_row):
                    output_row['pick'] = 'base'
                else:
                    output_row['pick'] = 'base'  # Default to base even if invalid
                writer.writerow(output_row)
                base_row = next(base_reader, None)
                
            elif new_cp < base_cp:
                # Character only in new font
                output_row = base_row.copy() if base_row else {}
                # Fill with new font data, but preserve base structure
                for key in output_fields:
                    if key == 'pick':
                        if is_valid_glyph(new_row):
                            output_row['pick'] = 'new'
                        else:
                            output_row['pick'] = 'base'
                    elif key in new_row:
                        output_row[key] = new_row[key]
                    elif key not in output_row:
                        output_row[key] = ''
                writer.writerow(output_row)
                new_row = next(new_reader, None)
                
            else:
                # Character in both fonts (base_cp == new_cp)
                output_row = base_row.copy()
                
                # Apply picking logic
                if is_valid_glyph(base_row):
                    output_row['pick'] = 'base'
                elif is_valid_glyph(new_row):
                    output_row['pick'] = 'new'
                else:
                    output_row['pick'] = 'base'
                
                writer.writerow(output_row)
                base_row = next(base_reader, None)
                new_row = next(new_reader, None)
    
    finally:
        base_file.close()
        new_file.close()
        out_file.close()


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description='Pick font source for each character based on availability and metrics'
    )
    parser.add_argument(
        'input_base_csv',
        help='Base font CSV file (from dump_char_csv.py)'
    )
    parser.add_argument(
        'input_new_csv',
        help='New font CSV file (from dump_char_csv.py)'
    )
    parser.add_argument(
        'output_csv',
        help='Output CSV file with pick column'
    )
    
    args = parser.parse_args()
    
    pick_font_sources(args.input_base_csv, args.input_new_csv, args.output_csv)
    print(f"Font picking complete. Output written to: {args.output_csv}")


if __name__ == '__main__':
    main()
