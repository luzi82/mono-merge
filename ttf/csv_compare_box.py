#!/usr/bin/env python3
"""
Compare character bounding box metrics between two CSV files.
Reports differences in advance width, positions, and other glyph properties.
"""

import argparse
import csv
import sys


def load_csv_by_codepoint(csv_path):
    """
    Load CSV file and index by codepoint_dec.
    
    Args:
        csv_path: Path to CSV file created by ttf/dump_char_csv.py
        
    Returns:
        Dictionary mapping codepoint_dec to row data
    """
    data = {}
    with open(csv_path, 'r', encoding='utf-8', newline='') as f:
        reader = csv.DictReader(f)
        for row in reader:
            codepoint = int(row['codepoint_dec'])
            data[codepoint] = row
    return data


def compare_csvs(csv_0_path, csv_1_path):
    """
    Compare two character CSV files and report differences.
    
    Args:
        csv_0_path: Path to first CSV file
        csv_1_path: Path to second CSV file
    """
    print(f"Loading {csv_0_path}...")
    data_0 = load_csv_by_codepoint(csv_0_path)
    
    print(f"Loading {csv_1_path}...")
    data_1 = load_csv_by_codepoint(csv_1_path)
    
    # Fields to compare
    fields_to_compare = [
        'lsb',
        'xMin',
        'yMin',
        'xMax',
        'yMax',
        'width',
        'height',
        'is_full_width',
        'is_empty_glyph',
        'is_composite',
        'num_contours'
    ]
    
    # Get all codepoints from both files
    all_codepoints = sorted(set(data_0.keys()) | set(data_1.keys()))
    
    print(f"\nComparing {len(all_codepoints)} codepoints...")
    print(f"CSV 0: {len(data_0)} characters")
    print(f"CSV 1: {len(data_1)} characters")
    print()
    
    mismatch_count = 0
    missing_in_0 = 0
    missing_in_1 = 0
    
    for codepoint in all_codepoints:
        row_0 = data_0.get(codepoint)
        row_1 = data_1.get(codepoint)
        
        # Check if codepoint exists in both files
        if row_0 is None:
            missing_in_0 += 1
            print(f"U+{codepoint:04X} ({codepoint}): MISSING in CSV 0 (exists in CSV 1)")
            continue
        
        if row_1 is None:
            missing_in_1 += 1
            print(f"U+{codepoint:04X} ({codepoint}): MISSING in CSV 1 (exists in CSV 0)")
            continue
        
        # Compare fields
        differences = []
        for field in fields_to_compare:
            val_0 = row_0.get(field, '')
            val_1 = row_1.get(field, '')
            
            if val_0 != val_1:
                differences.append(f"{field}: {val_0} vs {val_1}")
        
        if differences:
            mismatch_count += 1
            glyph_name_0 = row_0.get('glyph_name', '?')
            glyph_name_1 = row_1.get('glyph_name', '?')
            char_info = f"U+{codepoint:04X} ({codepoint})"
            
            if glyph_name_0 == glyph_name_1:
                print(f"{char_info} '{glyph_name_0}':")
            else:
                print(f"{char_info} '{glyph_name_0}' vs '{glyph_name_1}':")
            
            for diff in differences:
                print(f"  {diff}")
    
    # Print summary
    print()
    print("=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print(f"Total codepoints compared: {len(all_codepoints)}")
    print(f"Missing in CSV 0: {missing_in_0}")
    print(f"Missing in CSV 1: {missing_in_1}")
    print(f"Codepoints with differences: {mismatch_count}")
    
    if mismatch_count == 0 and missing_in_0 == 0 and missing_in_1 == 0:
        print("\n✓ All compared fields match!")
        return 0
    else:
        print(f"\n✗ Found {mismatch_count + missing_in_0 + missing_in_1} total differences")
        return 1


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description='Compare character bounding box metrics between two CSV files',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Example:
  %(prog)s output/test.char.csv output/expected.char.csv
        """
    )
    
    parser.add_argument(
        'input_csv_0',
        help='First CSV file (created by ttf/dump_char_csv.py)'
    )
    
    parser.add_argument(
        'input_csv_1',
        help='Second CSV file (created by ttf/dump_char_csv.py)'
    )
    
    args = parser.parse_args()
    
    try:
        exit_code = compare_csvs(args.input_csv_0, args.input_csv_1)
        sys.exit(exit_code)
    except FileNotFoundError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()
