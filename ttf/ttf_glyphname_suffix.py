#!/usr/bin/env python3

import argparse
from fontTools.ttLib import TTFont


def add_suffix_to_glyph_names(input_ttf, suffix, output_ttf):
    """Add suffix to all glyph names in the font."""
    font = TTFont(input_ttf)
    
    # Build a mapping of old glyph names to new glyph names
    old_to_new = {}
    glyph_order = font.getGlyphOrder()
    
    for old_name in glyph_order:
        # Skip .notdef - don't rename it
        if old_name == '.notdef':
            old_to_new[old_name] = old_name
        else:
            new_name = old_name + suffix
            old_to_new[old_name] = new_name
    
    # Update glyf table if it exists
    if 'glyf' in font:
        glyf = font['glyf']
        # Create new glyphs dict with renamed keys
        new_glyphs = {}
        for old_name in list(glyf.glyphs.keys()):
            new_name = old_to_new.get(old_name, old_name)
            glyph = glyf.glyphs[old_name]
            
            # Update component references if this is a composite glyph
            if hasattr(glyph, 'isComposite'):
                try:
                    if glyph.isComposite() and hasattr(glyph, 'components'):
                        for component in glyph.components:
                            component.glyphName = old_to_new.get(component.glyphName, component.glyphName)
                except:
                    pass  # Skip if glyph data is not fully loaded
            
            new_glyphs[new_name] = glyph
        
        glyf.glyphs = new_glyphs
    
    # Update hmtx table
    if 'hmtx' in font:
        hmtx = font['hmtx']
        new_metrics = {}
        for old_name in list(hmtx.metrics.keys()):
            new_name = old_to_new.get(old_name, old_name)
            new_metrics[new_name] = hmtx.metrics[old_name]
        hmtx.metrics = new_metrics
    
    # Update vmtx table if exists
    if 'vmtx' in font:
        vmtx = font['vmtx']
        new_metrics = {}
        for old_name in list(vmtx.metrics.keys()):
            new_name = old_to_new.get(old_name, old_name)
            new_metrics[new_name] = vmtx.metrics[old_name]
        vmtx.metrics = new_metrics
    
    # Update CFF table if it exists
    if 'CFF ' in font:
        cff = font['CFF '].cff[0]
        charstrings = cff.CharStrings
        new_charstrings = {}
        for old_name in list(charstrings.keys()):
            new_name = old_to_new.get(old_name, old_name)
            new_charstrings[new_name] = charstrings[old_name]
        charstrings.charStrings = new_charstrings
    
    # Update cmap table
    if 'cmap' in font:
        for table in font['cmap'].tables:
            new_cmap = {}
            for codepoint, old_name in table.cmap.items():
                new_name = old_to_new.get(old_name, old_name)
                new_cmap[codepoint] = new_name
            table.cmap = new_cmap
    
    # Update post table and convert to format 2.0 if needed
    if 'post' in font:
        post = font['post']
        # Only convert to format 2.0 if the font has a reasonable number of glyphs
        # Format 2.0 has limitations with large glyph counts
        num_glyphs = len(font.getGlyphOrder())
        if post.formatType == 3.0 and num_glyphs < 32768:
            # Try to convert to format 2.0 to store custom glyph names
            post.formatType = 2.0
            # Rebuild the mapping for format 2.0
            post.mapping = {}
            post.extraNames = []
        # If too many glyphs or already format 2.0, leave as is
    
    # Update glyph order
    font.setGlyphOrder([old_to_new[name] for name in glyph_order])
    
    # Save the modified font
    try:
        font.save(output_ttf)
    except OverflowError:
        # If format 2.0 fails due to too many glyphs, revert to format 3.0
        if 'post' in font and font['post'].formatType == 2.0:
            print("Warning: Too many glyphs for post table format 2.0, reverting to 3.0")
            font['post'].formatType = 3.0
            if hasattr(font['post'], 'mapping'):
                delattr(font['post'], 'mapping')
            if hasattr(font['post'], 'extraNames'):
                delattr(font['post'], 'extraNames')
            font.save(output_ttf)
    renamed_count = sum(1 for old, new in old_to_new.items() if old != new)
    print(f"Saved font with suffix '{suffix}' to {output_ttf}")
    print(f"Renamed {renamed_count} glyphs (excluding .notdef)")


def main():
    parser = argparse.ArgumentParser(
        description='Add suffix to all glyph names in a TrueType/OpenType font'
    )
    parser.add_argument('input_ttf', help='Input TTF/OTF file')
    parser.add_argument('suffix', help='Suffix to add to glyph names')
    parser.add_argument('output_ttf', help='Output TTF/OTF file')
    
    args = parser.parse_args()
    
    add_suffix_to_glyph_names(args.input_ttf, args.suffix, args.output_ttf)


if __name__ == '__main__':
    main()
