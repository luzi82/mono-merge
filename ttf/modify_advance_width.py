#!/usr/bin/env python3
"""
Modify advance width and x position of glyphs in a font.
"""

import argparse
import csv
from fontTools.ttLib import TTFont


def modify_advance_width(input_ttf, shift_x_csv, output_ttf):
    """
    Modify advance width and shift glyphs horizontally based on CSV data.
    
    Args:
        input_ttf: Path to the input TTF font file
        shift_x_csv: Path to CSV file with shift_x and advance_width columns
        output_ttf: Path to the output TTF font file
    """
    print(f"Loading font: {input_ttf}")
    font = TTFont(input_ttf)
    
    # Read shift data from CSV
    print(f"Reading shift data from: {shift_x_csv}")
    shift_data = {}  # glyph_index -> (shift_x, advance_width)
    
    with open(shift_x_csv, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            glyph_index = int(row['glyph_index'])
            shift_x = float(row['shift_x'])
            advance_width = int(row['advance_width'])
            shift_data[glyph_index] = (shift_x, advance_width)
    
    print(f"Loaded shift data for {len(shift_data)} glyphs")
    
    # Get glyph order to map glyph index to glyph name
    glyph_order = font.getGlyphOrder()
    
    # Get tables
    glyf_table = font['glyf']
    hmtx = font['hmtx']
    
    # Track which glyphs have been shifted to avoid double-shifting
    shifted_glyphs = set()
    
    # Process each glyph
    modified_count = 0
    for glyph_index, (shift_x, advance_width) in shift_data.items():
        # Get glyph name from glyph index
        if glyph_index >= len(glyph_order):
            print(f"Warning: glyph_index {glyph_index} out of range")
            continue
        
        glyph_name = glyph_order[glyph_index]
        
        if shift_x == 0:
            # Only update advance width, no shift needed
            try:
                old_advance_width, lsb = hmtx[glyph_name]
                hmtx[glyph_name] = (advance_width, lsb)
                modified_count += 1
            except KeyError:
                pass
            continue
        
        # Update advance width
        try:
            old_advance_width, lsb = hmtx[glyph_name]
            new_lsb = int(lsb + shift_x)
            hmtx[glyph_name] = (advance_width, new_lsb)
        except KeyError:
            pass
        
        # Shift glyph coordinates (only if not already shifted)
        if glyph_name not in glyf_table:
            continue
        
        if glyph_name in shifted_glyphs:
            # Already shifted this glyph, skip to avoid double-shifting
            continue
        
        glyph = glyf_table[glyph_name]
        shift_x_int = int(shift_x)
        
        if glyph.isComposite():
            # For composite glyphs, adjust component translations
            for comp in glyph.components:
                comp.x += shift_x_int
        elif glyph.numberOfContours > 0:
            # For simple glyphs, shift all x coordinates
            coords = glyph.coordinates
            for i in range(len(coords)):
                x, y = coords[i]
                coords[i] = (x + shift_x_int, y)
        
        shifted_glyphs.add(glyph_name)
        modified_count += 1
    
    print(f"Modified {modified_count} glyphs")
    
    # Save the modified font
    print(f"Saving to: {output_ttf}")
    font.save(output_ttf)
    print("Done!")


def main():
    parser = argparse.ArgumentParser(
        description='Modify advance width and x position of glyphs in a font.'
    )
    parser.add_argument(
        'input_ttf',
        help='Input TTF font file'
    )
    parser.add_argument(
        'input_shift_x_csv',
        help='CSV file with glyph_index, shift_x and advance_width columns (created by cal_shift_x_csv.py, e.g. CodeCJK/build/tmp/patch0.z04.04.shift_x.csv)'
    )
    parser.add_argument(
        'output_ttf',
        help='Output TTF font file'
    )
    
    args = parser.parse_args()
    
    modify_advance_width(args.input_ttf, args.input_shift_x_csv, args.output_ttf)


if __name__ == '__main__':
    main()
