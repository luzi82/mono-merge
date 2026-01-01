#!/usr/bin/env python3
"""
Mark glyphs for removal based on usage.
Adds an 'rm' column to the glyph CSV: rm=1 if glyph is not referenced by any codepoint
directly or indirectly (through composite glyph references), else rm=0.
.notdef is always kept (rm=0).
"""
import argparse
import csv
import sys
from collections import defaultdict, deque


def mark_glyphs_for_removal(input_glyph_csv, input_glyphref_csv, output_csv):
    """
    Read glyph CSV and glyphref CSV, add an 'rm' column indicating whether the glyph should be removed.
    
    Args:
        input_glyph_csv: Path to input glyph CSV file (created by dump_char_csv.py)
        input_glyphref_csv: Path to input glyphref CSV file (created by dump_char_csv.py)
        output_csv: Path to output CSV file with 'rm' column added
    """
    # Build glyphref graph from glyphref CSV
    glyphref_graph = defaultdict(set)  # ref_from -> set of ref_to
    try:
        with open(input_glyphref_csv, 'r', newline='', encoding='utf-8') as reffile:
            ref_reader = csv.DictReader(reffile)
            
            if 'ref_from' not in ref_reader.fieldnames or 'ref_to' not in ref_reader.fieldnames:
                print("Error: Glyphref CSV must contain 'ref_from' and 'ref_to' columns", file=sys.stderr)
                sys.exit(1)
            
            for row in ref_reader:
                ref_from = row.get('ref_from', '')
                ref_to = row.get('ref_to', '')
                if ref_from and ref_to:
                    glyphref_graph[ref_from].add(ref_to)
    except FileNotFoundError:
        print(f"Error: Glyphref file '{input_glyphref_csv}' not found", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Error reading glyphref CSV: {e}", file=sys.stderr)
        sys.exit(1)
    
    # Process glyph CSV
    try:
        with open(input_glyph_csv, 'r', newline='', encoding='utf-8') as infile:
            reader = csv.DictReader(infile)
            fieldnames = reader.fieldnames
            
            # Validate required columns exist
            if 'glyph_name' not in fieldnames or 'cmap_used' not in fieldnames:
                print("Error: Input CSV must contain 'glyph_name' and 'cmap_used' columns", file=sys.stderr)
                sys.exit(1)
            
            # Add 'rm' column to fieldnames if not already present
            if 'rm' not in fieldnames:
                fieldnames = list(fieldnames) + ['rm']
            
            # First pass: collect all glyphs and identify cmap-referenced glyphs
            all_glyphs = {}
            cmap_referenced_glyphs = set()
            
            for row in reader:
                glyph_name = row.get('glyph_name', '')
                all_glyphs[glyph_name] = row
                
                # Check if glyph is directly referenced by cmap
                try:
                    cmap_used = int(row.get('cmap_used', 0) or 0)
                    if cmap_used > 0:
                        cmap_referenced_glyphs.add(glyph_name)
                except ValueError:
                    pass
            
            # Second pass: find all glyphs reachable from cmap-referenced glyphs
            # Use BFS to traverse composite glyph references
            reachable_glyphs = set(cmap_referenced_glyphs)
            queue = deque(cmap_referenced_glyphs)
            
            while queue:
                current_glyph = queue.popleft()
                # Add all glyphs referenced by this glyph
                if current_glyph in glyphref_graph:
                    for ref_to in glyphref_graph[current_glyph]:
                        if ref_to not in reachable_glyphs:
                            reachable_glyphs.add(ref_to)
                            queue.append(ref_to)
            
            # Third pass: mark glyphs for removal
            rows = []
            for glyph_name, row in all_glyphs.items():
                # Never remove .notdef
                if glyph_name == '.notdef':
                    row['rm'] = 0
                # Remove if not reachable from any codepoint
                elif glyph_name not in reachable_glyphs:
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
        print(f"Glyphs reachable from cmap: {len(reachable_glyphs)}")
        
    except FileNotFoundError:
        print(f"Error: Input file '{input_glyph_csv}' not found", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Error processing CSV: {e}", file=sys.stderr)
        sys.exit(1)


def main():
    parser = argparse.ArgumentParser(
        description='Mark glyphs for removal based on cmap reachability (direct and indirect through composite glyphs)'
    )
    parser.add_argument('input_glyph_csv', help='Input glyph CSV file (created by dump_char_csv.py)')
    parser.add_argument('input_glyphref_csv', help='Input glyphref CSV file (created by dump_char_csv.py)')
    parser.add_argument('output_csv', help='Output CSV file with rm column added')
    
    args = parser.parse_args()
    
    mark_glyphs_for_removal(args.input_glyph_csv, args.input_glyphref_csv, args.output_csv)


if __name__ == '__main__':
    main()
