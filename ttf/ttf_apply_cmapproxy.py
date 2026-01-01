#!/usr/bin/env python3

import argparse
import csv
from fontTools.ttLib import TTFont
from fontTools.pens.t2CharStringPen import T2CharStringPen
from fontTools.pens.ttGlyphPen import TTGlyphPen


def main():
    parser = argparse.ArgumentParser(
        description='Apply cmap proxy glyphs to a TTF font'
    )
    parser.add_argument('input_ttf', help='Input TTF file')
    parser.add_argument('input_cmapproxy_csv', help='Input cmapproxy CSV file')
    parser.add_argument('output_ttf', help='Output TTF file')
    
    args = parser.parse_args()
    
    # Load the font
    font = TTFont(args.input_ttf)
    
    # Read the cmapproxy CSV
    proxy_mappings = []
    with open(args.input_cmapproxy_csv, 'r', newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            proxy_mappings.append({
                'old_glyph_name': row['old_glyph_name'],
                'new_glyph_name': row['new_glyph_name']
            })
    
    # Get the glyf and hmtx tables
    glyf_table = font['glyf']
    hmtx_table = font['hmtx']
    
    # Get the current glyph order and create a glyph set
    glyph_order = list(font.getGlyphOrder())
    glyph_set = font.getGlyphSet()
    
    # Create composite glyphs for each proxy
    for mapping in proxy_mappings:
        old_glyph_name = mapping['old_glyph_name']
        new_glyph_name = mapping['new_glyph_name']
        
        # Create a composite glyph that references the old glyph
        pen = TTGlyphPen(glyph_set)
        
        # Add a component that references the old glyph with identity transformation
        pen.addComponent(old_glyph_name, (1, 0, 0, 1, 0, 0))
        
        # Get the new glyph from the pen
        new_glyph = pen.glyph()
        
        # Add the new glyph to the glyf table
        glyf_table[new_glyph_name] = new_glyph
        
        # Copy the advance width and left side bearing from the old glyph
        if old_glyph_name in hmtx_table.metrics:
            hmtx_table.metrics[new_glyph_name] = hmtx_table.metrics[old_glyph_name]
        
        # Add to glyph order
        glyph_order.append(new_glyph_name)
    
    # Update the font's glyph order
    font.setGlyphOrder(glyph_order)
    
    # Update maxp table
    font['maxp'].numGlyphs = len(glyph_order)
    
    # Ensure post table stores glyph names (convert to format 2.0 if needed)
    if font['post'].formatType == 3.0:
        font['post'].formatType = 2.0
        font['post'].extraNames = []
        font['post'].mapping = {}
        font['post'].glyphOrder = glyph_order
    
    # Update the cmap table to point to new glyphs
    for table in font['cmap'].tables:
        cmap = table.cmap
        # Build a list of updates to avoid modifying dict during iteration
        updates = []
        for codepoint, glyph_name in cmap.items():
            # Check if this codepoint points to an old glyph
            for mapping in proxy_mappings:
                if glyph_name == mapping['old_glyph_name']:
                    updates.append((codepoint, mapping['new_glyph_name']))
                    break
        
        # Apply the updates
        for codepoint, new_glyph_name in updates:
            cmap[codepoint] = new_glyph_name
    
    # Save the modified font
    font.save(args.output_ttf)
    print(f"Applied {len(proxy_mappings)} cmap proxy glyphs")
    print(f"Output saved to: {args.output_ttf}")


if __name__ == '__main__':
    main()
