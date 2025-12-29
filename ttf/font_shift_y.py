#!/usr/bin/env python3
"""
Shift all glyphs in a font vertically by a specified amount.
"""

import argparse
import yaml
from fontTools.ttLib import TTFont


def shift_font_y(input_ttf, shift_y):
    """
    Apply a vertical offset to all glyphs in the font.
    
    Args:
        input_ttf: Path to the input TTF font file
        shift_y: Vertical shift amount in font units
        
    Returns:
        Modified TTFont object
    """
    font = TTFont(input_ttf)
    
    if shift_y == 0:
        print("shift_y is 0, no changes needed")
        return font
    
    glyf_table = font['glyf']
    
    for glyph_name in font.getGlyphOrder():
        if glyph_name not in glyf_table:
            continue
        
        glyph = glyf_table[glyph_name]
        
        if glyph.isComposite():
            # For composite glyphs, adjust component translations
            for comp in glyph.components:
                comp.y += shift_y
        elif glyph.numberOfContours > 0:
            # For simple glyphs, shift all coordinates
            for coord_list in [glyph.coordinates]:
                for i in range(len(coord_list)):
                    x, y = coord_list[i]
                    coord_list[i] = (x, y + shift_y)
    
    return font


def main():
    parser = argparse.ArgumentParser(
        description='Shift all glyphs in a font vertically by a specified amount.'
    )
    parser.add_argument(
        'input_ttf',
        help='Input TTF font file (e.g., input/NotoSansMonoCJKhk-VF.ttf)'
    )
    parser.add_argument(
        'input_shift_yaml',
        help='Input YAML file containing shift_y value (e.g., output/shift.yaml)'
    )
    parser.add_argument(
        'output_ttf',
        help='Output TTF font file'
    )
    
    args = parser.parse_args()
    
    # Read shift_y value from YAML
    with open(args.input_shift_yaml, 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)
    
    shift_y = config.get('shift_y', 0)
    
    print(f"Loading font: {args.input_ttf}")
    print(f"Applying shift_y: {shift_y}")
    
    # Apply the shift
    font = shift_font_y(args.input_ttf, shift_y)
    
    # Save the modified font
    print(f"Saving to: {args.output_ttf}")
    font.save(args.output_ttf)
    
    print("Done!")


if __name__ == '__main__':
    main()
