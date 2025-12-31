#!/usr/bin/env python3
"""
Mark glyphs for removal based on usage.
Adds an 'rm' column to the glyph CSV: rm=1 if both cmap_used=0 and glyf_used=0, else rm=0.
"""
import argparse
import csv
import sys


def mark_glyphs_for_removal(input_csv, output_csv):
    """
    Read glyph CSV and add an 'rm' column indicating whether the glyph should be removed.
    
    Args:
        input_csv: Path to input glyph CSV file (created by dump_char_csv.py)
        output_csv: Path to output CSV file with 'rm' column added
    """
    try:
        with open(input_csv, 'r', newline='', encoding='utf-8') as infile:
            reader = csv.DictReader(infile)
            fieldnames = reader.fieldnames
            
            # Validate required columns exist
            if 'cmap_used' not in fieldnames or 'glyf_used' not in fieldnames:
                print("Error: Input CSV must contain 'cmap_used' and 'glyf_used' columns", file=sys.stderr)
                sys.exit(1)
            
            # Add 'rm' column to fieldnames if not already present
            if 'rm' not in fieldnames:
                fieldnames = list(fieldnames) + ['rm']
            
            rows = []
            for row in reader:
                # Parse usage counts (handle empty strings as 0)
                try:
                    cmap_used = int(row.get('cmap_used', 0) or 0)
                    glyf_used = int(row.get('glyf_used', 0) or 0)
                except ValueError:
                    print(f"Warning: Invalid usage count for glyph {row.get('glyph_name', 'unknown')}", file=sys.stderr)
                    cmap_used = 0
                    glyf_used = 0
                
                # Determine if glyph should be removed
                if cmap_used == 0 and glyf_used == 0:
                    row['rm'] = 1
                else:
                    row['rm'] = 0
                
                rows.append(row)
        
        # Write output CSV
        with open(output_csv, 'w', newline='', encoding='utf-8') as outfile:
            writer = csv.DictWriter(outfile, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(rows)
        
        print(f"Successfully processed {len(rows)} glyphs")
        glyphs_to_remove = sum(1 for row in rows if row['rm'] == 1)
        print(f"Glyphs marked for removal: {glyphs_to_remove}")
        
    except FileNotFoundError:
        print(f"Error: Input file '{input_csv}' not found", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Error processing CSV: {e}", file=sys.stderr)
        sys.exit(1)


def main():
    parser = argparse.ArgumentParser(
        description='Mark glyphs for removal based on cmap_used and glyf_used columns'
    )
    parser.add_argument('input_csv', help='Input glyph CSV file (created by dump_char_csv.py)')
    parser.add_argument('output_csv', help='Output CSV file with rm column added')
    
    args = parser.parse_args()
    
    mark_glyphs_for_removal(args.input_csv, args.output_csv)


if __name__ == '__main__':
    main()
