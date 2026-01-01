#!/usr/bin/env python3

import argparse
import csv
from fontTools.ttLib import TTFont
from fontTools.pens.ttGlyphPen import TTGlyphPen


def main():
    parser = argparse.ArgumentParser(
        description='Apply cmap proxy glyphs to a TTF font using glyph indices'
    )
    parser.add_argument('input_ttf', help='Input TTF file')
    parser.add_argument('input_cmapproxy_csv', help='Input cmapproxy CSV file with old_glyph_index and new_glyph_index columns')
    parser.add_argument('output_ttf', help='Output TTF file')
    
    args = parser.parse_args()
    
    # Load the font
    font = TTFont(args.input_ttf)
    
    # Check that post table is format 3.0
    if font['post'].formatType != 3.0:
        raise ValueError(f"Font post table formatType must be 3.0, but is {font['post'].formatType}")
    
    # Read the cmapproxy CSV
    proxy_mappings = []
    with open(args.input_cmapproxy_csv, 'r', newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            proxy_mappings.append({
                'old_glyph_index': int(row['old_glyph_index']),
                'new_glyph_index': int(row['new_glyph_index'])
            })
    
    # Get the glyf and hmtx tables
    glyf_table = font['glyf']
    hmtx_table = font['hmtx']
    
    # Get the current glyph order
    glyph_order = list(font.getGlyphOrder())
    
    # Build a reverse mapping from index to glyph name
    index_to_name = {i: glyph_order[i] for i in range(len(glyph_order))}
    
    # Prepare to extend glyph order with new proxy glyphs
    new_glyphs = {}
    
    # Create composite glyphs for each proxy
    for mapping in proxy_mappings:
        old_glyph_index = mapping['old_glyph_index']
        new_glyph_index = mapping['new_glyph_index']
        
        # Get the old glyph name
        old_glyph_name = index_to_name.get(old_glyph_index)
        if old_glyph_name is None:
            raise ValueError(f"Old glyph index {old_glyph_index} not found in font")
        
        # Generate a placeholder name for the new glyph (post table v3 won't use it)
        new_glyph_name = f"glyph{new_glyph_index:05d}"
        
        # Ensure the new index is valid
        if new_glyph_index < len(glyph_order):
            raise ValueError(f"New glyph index {new_glyph_index} conflicts with existing glyph at that position")
        
        # Create a glyph set for the pen
        glyph_set = font.getGlyphSet()
        
        # Create a composite glyph that references the old glyph
        pen = TTGlyphPen(glyph_set)
        
        # Add a component that references the old glyph index with identity transformation
        pen.addComponent(old_glyph_name, (1, 0, 0, 1, 0, 0))
        
        # Get the new glyph from the pen
        new_glyph = pen.glyph()
        
        # Store for later addition
        new_glyphs[new_glyph_index] = {
            'name': new_glyph_name,
            'glyph': new_glyph,
            'old_glyph_name': old_glyph_name,
            'old_glyph_index': old_glyph_index
        }
    
    # Sort new glyphs by index to ensure they're added in order
    sorted_new_indices = sorted(new_glyphs.keys())
    
    # Extend the glyph order to accommodate new glyphs
    max_new_index = max(sorted_new_indices) if sorted_new_indices else len(glyph_order) - 1
    while len(glyph_order) <= max_new_index:
        glyph_order.append(f".notdef_{len(glyph_order)}")
    
    # Add new glyphs at their designated indices
    for new_glyph_index in sorted_new_indices:
        info = new_glyphs[new_glyph_index]
        new_glyph_name = info['name']
        new_glyph = info['glyph']
        old_glyph_name = info['old_glyph_name']
        
        # Replace the placeholder at the index with the actual glyph name
        glyph_order[new_glyph_index] = new_glyph_name
        
        # Add the new glyph to the glyf table
        glyf_table[new_glyph_name] = new_glyph
        
        # Copy the advance width and left side bearing from the old glyph
        if old_glyph_name in hmtx_table.metrics:
            hmtx_table.metrics[new_glyph_name] = hmtx_table.metrics[old_glyph_name]
        
        # Update the index-to-name mapping
        index_to_name[new_glyph_index] = new_glyph_name
    
    # Update the font's glyph order
    font.setGlyphOrder(glyph_order)
    
    # Update maxp table
    font['maxp'].numGlyphs = len(glyph_order)
    
    # Build a mapping from old glyph index to new glyph name for cmap updates
    old_index_to_new_name = {}
    for mapping in proxy_mappings:
        old_glyph_index = mapping['old_glyph_index']
        new_glyph_index = mapping['new_glyph_index']
        old_glyph_name = index_to_name.get(old_glyph_index)
        new_glyph_name = index_to_name.get(new_glyph_index)
        if old_glyph_name and new_glyph_name:
            old_index_to_new_name[old_glyph_name] = new_glyph_name
    
    # Update the cmap table to point to new glyphs
    for table in font['cmap'].tables:
        cmap = table.cmap
        # Build a list of updates to avoid modifying dict during iteration
        updates = []
        for codepoint, glyph_name in cmap.items():
            # Check if this codepoint points to an old glyph that should be proxied
            if glyph_name in old_index_to_new_name:
                updates.append((codepoint, old_index_to_new_name[glyph_name]))
        
        # Apply the updates
        for codepoint, new_glyph_name in updates:
            cmap[codepoint] = new_glyph_name
    
    # Save the modified font
    font.save(args.output_ttf)
    print(f"Applied {len(proxy_mappings)} cmap proxy glyphs")
    print(f"Output saved to: {args.output_ttf}")


if __name__ == '__main__':
    main()
