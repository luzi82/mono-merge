#!/usr/bin/env python3
"""
Remove glyphs from a TTF file based on a CSV marking file.
Removes glyphs where rm=1 from the font.
"""
import argparse
import csv
import sys
from fontTools.ttLib import TTFont
from fontTools import subset


def load_glyphs_to_remove(input_csv):
    """
    Load the list of glyph names to remove from the CSV file.
    
    Args:
        input_csv: Path to CSV file with rm column
    
    Returns:
        Set of glyph names where rm=1
    """
    glyphs_to_remove = set()
    
    try:
        with open(input_csv, 'r', newline='', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile)
            
            if 'glyph_name' not in reader.fieldnames or 'rm' not in reader.fieldnames:
                print("Error: CSV must contain 'glyph_name' and 'rm' columns", file=sys.stderr)
                sys.exit(1)
            
            for row in reader:
                glyph_name = row.get('glyph_name', '')
                rm_value = row.get('rm', '0')
                
                try:
                    if int(rm_value) == 1:
                        glyphs_to_remove.add(glyph_name)
                except ValueError:
                    print(f"Warning: Invalid rm value for glyph {glyph_name}", file=sys.stderr)
        
        return glyphs_to_remove
    
    except FileNotFoundError:
        print(f"Error: CSV file '{input_csv}' not found", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Error reading CSV: {e}", file=sys.stderr)
        sys.exit(1)


def remove_glyphs_from_font(font, glyphs_to_remove):
    """
    Remove specified glyphs from the font using fontTools subsetter.
    
    Args:
        font: TTFont object
        glyphs_to_remove: Set of glyph names to remove
    """
    if not glyphs_to_remove:
        print("No glyphs to remove")
        return
    
    # Check if .notdef is in glyphs_to_remove
    if '.notdef' in glyphs_to_remove:
        raise ValueError("Cannot remove .notdef glyph - it is required in all fonts")
    
    # Check if any glyph to remove is still mapped in cmap
    if 'cmap' in font:
        mapped_glyphs = set()
        for table in font['cmap'].tables:
            for codepoint, glyph_name in table.cmap.items():
                if glyph_name in glyphs_to_remove:
                    mapped_glyphs.add((glyph_name, codepoint))
        
        if mapped_glyphs:
            error_msg = "Cannot remove glyphs that are still mapped in cmap:\n"
            for glyph_name, codepoint in sorted(mapped_glyphs):
                error_msg += f"  {glyph_name} -> U+{codepoint:04X}\n"
            raise ValueError(error_msg)
    
    # Get the current glyph order
    glyph_order = font.getGlyphOrder()
    
    # Count and list glyphs to remove
    removed_count = 0
    for glyph_name in glyph_order:
        if glyph_name in glyphs_to_remove:
            print(f"Removing glyph: {glyph_name}")
            removed_count += 1
    
    if removed_count == 0:
        print("No glyphs were removed")
        return
    
    # Create list of glyphs to keep
    glyphs_to_keep = [g for g in glyph_order if g not in glyphs_to_remove]
    
    # Use fontTools subsetter to properly remove glyphs
    options = subset.Options()
    options.drop_tables = []  # Don't drop any tables
    subsetter = subset.Subsetter(options=options)
    subsetter.populate(glyphs=glyphs_to_keep)
    subsetter.subset(font)
    
    print(f"Removed {removed_count} glyphs")
    print(f"Remaining glyphs: {len(glyphs_to_keep)}")


def main():
    parser = argparse.ArgumentParser(
        description='Remove glyphs from TTF file based on CSV marking file'
    )
    parser.add_argument('input_ttf', help='Input TTF file')
    parser.add_argument('input_rm_glyph_csv', help='CSV file with rm column (created by glyphcsv_used_mark_rm.py)')
    parser.add_argument('output_ttf', help='Output TTF file')
    
    args = parser.parse_args()
    
    # Load glyphs to remove from CSV
    print(f"Reading CSV: {args.input_rm_glyph_csv}")
    glyphs_to_remove = load_glyphs_to_remove(args.input_rm_glyph_csv)
    print(f"Found {len(glyphs_to_remove)} glyphs marked for removal")
    
    # Load font
    print(f"Loading font: {args.input_ttf}")
    try:
        font = TTFont(args.input_ttf)
    except Exception as e:
        print(f"Error loading font: {e}", file=sys.stderr)
        sys.exit(1)
    
    # Remove glyphs
    remove_glyphs_from_font(font, glyphs_to_remove)
    
    # Save modified font
    print(f"Saving font: {args.output_ttf}")
    try:
        font.save(args.output_ttf)
        print("Done!")
    except Exception as e:
        print(f"Error saving font: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()
