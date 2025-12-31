#!/usr/bin/env python3
"""
Dump TTF character information to CSV file.
Outputs one row per character with codepoint, bounding box, advance width, glyph name, and other metadata.
"""
import argparse
import csv
import sys
from fontTools.ttLib import TTFont


def dump_font_to_csv(input_ttf, output_csv):
    """
    Extract character information from TTF file and write to CSV.
    
    Args:
        input_ttf: Path to input TTF file
        output_csv: Path to output CSV file
    """
    try:
        font = TTFont(input_ttf)
    except Exception as e:
        print(f"Error loading font: {e}", file=sys.stderr)
        sys.exit(1)
    
    # Get necessary tables
    cmap = font.getBestCmap()
    if not cmap:
        print("Error: No suitable cmap found in font", file=sys.stderr)
        sys.exit(1)
    
    glyf = font.get('glyf')
    hmtx = font.get('hmtx')
    head = font.get('head')
    
    if not glyf:
        print("Error: No glyf table found (not a TrueType font?)", file=sys.stderr)
        sys.exit(1)
    
    if not hmtx:
        print("Error: No hmtx table found", file=sys.stderr)
        sys.exit(1)
    
    # Determine reference width for full-width detection (use space character U+0020)
    reference_width = None
    if 0x0020 in cmap:  # ASCII space
        space_glyph = cmap[0x0020]
        if space_glyph in hmtx.metrics:
            reference_width, _ = hmtx.metrics[space_glyph]
    
    # If space not found, try 'A' (U+0041)
    if reference_width is None and 0x0041 in cmap:
        a_glyph = cmap[0x0041]
        if a_glyph in hmtx.metrics:
            reference_width, _ = hmtx.metrics[a_glyph]
    
    # Prepare CSV data
    rows = []
    
    for codepoint in sorted(cmap.keys()):
        glyph_name = cmap[codepoint]
        
        # Get horizontal metrics
        advance_width = None
        lsb = None
        if glyph_name in hmtx.metrics:
            advance_width, lsb = hmtx.metrics[glyph_name]
        
        # Get glyph bounding box
        xMin, yMin, xMax, yMax = None, None, None, None
        is_composite = None
        num_contours = None
        
        if glyph_name in glyf:
            glyph = glyf[glyph_name]
            is_composite = glyph.isComposite()
            
            if hasattr(glyph, 'xMin'):
                xMin = glyph.xMin
                yMin = glyph.yMin
                xMax = glyph.xMax
                yMax = glyph.yMax
            
            if hasattr(glyph, 'numberOfContours'):
                num_contours = glyph.numberOfContours
        
        # Determine if character is full-width
        is_full_width = None
        if reference_width is not None and advance_width is not None:
            # Full-width if advance_width is approximately 2x reference (within 10% tolerance)
            ratio = advance_width / reference_width
            is_full_width = 1.8 <= ratio <= 2.2
        
        # Determine if glyph is empty (no contours or no bounding box)
        is_empty_glyph = (num_contours == 0) or (xMin is None)
        
        # Build row
        row = {
            'codepoint': f"U+{codepoint:04X}",
            'codepoint_dec': codepoint,
            'glyph_name': glyph_name,
            'advance_width': advance_width,
            'lsb': lsb,
            'xMin': xMin,
            'yMin': yMin,
            'xMax': xMax,
            'yMax': yMax,
            'width': (xMax - xMin) if (xMin is not None and xMax is not None) else None,
            'height': (yMax - yMin) if (yMin is not None and yMax is not None) else None,
            'is_full_width': is_full_width,
            'is_empty_glyph': is_empty_glyph,
            'is_composite': is_composite,
            'num_contours': num_contours,
        }
        rows.append(row)
    
    # Write to CSV
    fieldnames = [
        'codepoint',
        'codepoint_dec',
        'glyph_name',
        'advance_width',
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
        'num_contours',
    ]
    
    try:
        with open(output_csv, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(rows)
        
        print(f"Successfully wrote {len(rows)} characters to {output_csv}")
    except Exception as e:
        print(f"Error writing CSV file: {e}", file=sys.stderr)
        sys.exit(1)
    
    font.close()


def main():
    parser = argparse.ArgumentParser(
        description="Dump TTF character information to CSV file."
    )
    parser.add_argument(
        "input_ttf",
        help="Path to input TTF file"
    )
    parser.add_argument(
        "output_csv",
        help="Path to output CSV file"
    )
    
    args = parser.parse_args()
    dump_font_to_csv(args.input_ttf, args.output_csv)


if __name__ == "__main__":
    main()
