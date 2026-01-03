#!/usr/bin/env python3
"""
Scale a font to match the advance width of another font.
"""

import argparse
import csv
import shutil
import sys
from fontTools.ttLib import TTFont
from fontTools.misc.transform import Transform
from fontTools.misc.fixedTools import floatToFixed


def get_char_advance_width(font, char):
    """
    Get the advance width of a character.
    
    Args:
        font: TTFont object
        char: Character to query (e.g., 'O')
        
    Returns:
        Advance width in font units, or None if character not found
    """
    cmap = font.getBestCmap()
    if cmap is None:
        return None
    
    codepoint = ord(char)
    if codepoint not in cmap:
        return None
    
    glyph_name = cmap[codepoint]
    hmtx = font['hmtx']
    advance_width, lsb = hmtx[glyph_name]
    return advance_width


def scale_font(font, scale_factor, glyphs_to_scale=None):
    """
    Scale a font by a given factor.
    
    Args:
        font: TTFont object
        scale_factor: Scaling factor (e.g., 1.2 for 120%)
        glyphs_to_scale: Set of glyph indices to scale (if None, scale all glyphs)
        
    Returns:
        Modified TTFont object
    """
    # Check for composite glyphs - not supported
    if 'glyf' in font:
        glyf_table = font['glyf']
        for glyph_name in font.getGlyphOrder():
            if glyph_name not in glyf_table:
                continue
            glyph = glyf_table[glyph_name]
            if glyph.isComposite():
                raise RuntimeError(
                    f"Font contains composite glyph '{glyph_name}'. "
                    f"Composite glyphs are not supported."
                )
    
    # Scale glyph coordinates
    if 'glyf' in font:
        glyf_table = font['glyf']
        for glyph_name in font.getGlyphOrder():
            if glyph_name not in glyf_table:
                continue
            
            # Skip if glyphs_to_scale is specified and this glyph is not in the set
            if glyphs_to_scale is not None:
                glyph_index = font.getGlyphID(glyph_name)
                if glyph_index not in glyphs_to_scale:
                    continue
            
            glyph = glyf_table[glyph_name]
            
            if glyph.numberOfContours > 0:
                # For simple glyphs, scale all coordinates
                coords = glyph.coordinates
                for i in range(len(coords)):
                    x, y = coords[i]
                    coords[i] = (int(x * scale_factor), int(y * scale_factor))
                # Remove hinting instructions as they're designed for original scale
                from fontTools.ttLib.tables._g_l_y_f import ttProgram
                glyph.program = ttProgram.Program()
    
    # Scale horizontal metrics (advance widths and left side bearings)
    if 'hmtx' in font:
        hmtx = font['hmtx']
        for glyph_name in font.getGlyphOrder():
            # Skip if glyphs_to_scale is specified and this glyph is not in the set
            if glyphs_to_scale is not None:
                glyph_index = font.getGlyphID(glyph_name)
                if glyph_index not in glyphs_to_scale:
                    continue
            try:
                advance_width, lsb = hmtx[glyph_name]
                hmtx[glyph_name] = (int(advance_width * scale_factor), int(lsb * scale_factor))
            except KeyError:
                pass
    
    # Vertical metrics should not exist per requirement
    if 'vmtx' in font:
        raise RuntimeError("Font contains vmtx table, which is not supported")
    
    # Only scale global font metrics if we're scaling ALL glyphs
    # If we're selectively scaling, these tables should remain unchanged
    if glyphs_to_scale is None:
        # Scale hhea table
        if 'hhea' in font:
            hhea = font['hhea']
            hhea.ascent = int(hhea.ascent * scale_factor)
            hhea.descent = int(hhea.descent * scale_factor)
            hhea.lineGap = int(hhea.lineGap * scale_factor)
            hhea.advanceWidthMax = int(hhea.advanceWidthMax * scale_factor)
            hhea.minLeftSideBearing = int(hhea.minLeftSideBearing * scale_factor)
            hhea.minRightSideBearing = int(hhea.minRightSideBearing * scale_factor)
            hhea.xMaxExtent = int(hhea.xMaxExtent * scale_factor)
        
        # Vertical metrics should not exist per requirement
        if 'vhea' in font:
            raise RuntimeError("Font contains vhea table, which is not supported")
        
        # Scale OS/2 table
        if 'OS/2' in font:
            os2 = font['OS/2']
            os2.xAvgCharWidth = int(os2.xAvgCharWidth * scale_factor)
            os2.sTypoAscender = int(os2.sTypoAscender * scale_factor)
            os2.sTypoDescender = int(os2.sTypoDescender * scale_factor)
            os2.sTypoLineGap = int(os2.sTypoLineGap * scale_factor)
            os2.usWinAscent = int(os2.usWinAscent * scale_factor)
            os2.usWinDescent = int(os2.usWinDescent * scale_factor)
            os2.sxHeight = int(os2.sxHeight * scale_factor)
            os2.sCapHeight = int(os2.sCapHeight * scale_factor)
            os2.ySubscriptXSize = int(os2.ySubscriptXSize * scale_factor)
            os2.ySubscriptYSize = int(os2.ySubscriptYSize * scale_factor)
            os2.ySubscriptXOffset = int(os2.ySubscriptXOffset * scale_factor)
            os2.ySubscriptYOffset = int(os2.ySubscriptYOffset * scale_factor)
            os2.ySuperscriptXSize = int(os2.ySuperscriptXSize * scale_factor)
            os2.ySuperscriptYSize = int(os2.ySuperscriptYSize * scale_factor)
            os2.ySuperscriptXOffset = int(os2.ySuperscriptXOffset * scale_factor)
            os2.ySuperscriptYOffset = int(os2.ySuperscriptYOffset * scale_factor)
            os2.yStrikeoutSize = int(os2.yStrikeoutSize * scale_factor)
            os2.yStrikeoutPosition = int(os2.yStrikeoutPosition * scale_factor)
        
        # Scale post table
        if 'post' in font:
            post = font['post']
            post.underlinePosition = int(post.underlinePosition * scale_factor)
            post.underlineThickness = int(post.underlineThickness * scale_factor)
        
        # Scale head table - bounding box
        if 'head' in font:
            head = font['head']
            head.xMin = int(head.xMin * scale_factor)
            head.yMin = int(head.yMin * scale_factor)
            head.xMax = int(head.xMax * scale_factor)
            head.yMax = int(head.yMax * scale_factor)
        
        # Scale maxp table - maxZones for hinting
        if 'maxp' in font:
            maxp = font['maxp']
            if hasattr(maxp, 'maxZones'):
                # maxZones relates to hinting zones, should be scaled
                pass  # Usually recalculated by fontTools
        
        # Scale cvt table (Control Value Table) for hinting
        if 'cvt ' in font:
            cvt = font['cvt ']
            for i in range(len(cvt.values)):
                cvt.values[i] = int(cvt.values[i] * scale_factor)
    
    # Scale fpgm and prep tables contain bytecode instructions
    # These are more complex and may need manual adjustment
    # For now, we'll leave them as-is and let the font renderer handle it
    
    # Note: units_per_em is NOT scaled as per requirement
    
    return font


def main():
    parser = argparse.ArgumentParser(
        description='Scale a font to match the advance width of another font.'
    )
    parser.add_argument(
        'input_ttf',
        help='The TTF font to be scaled'
    )
    parser.add_argument(
        'input_glyph_csv',
        help='CSV file with glyph information (e.g., CodeCJK/build/tmp/patch0.z01.00.ttf.glyph.csv)'
    )
    parser.add_argument(
        'scale_factor',
        type=float,
        help='Scale factor to apply (e.g., 1.2 for 120%%)'
    )
    parser.add_argument(
        'output_ttf',
        help='Output scaled TTF file'
    )
    
    args = parser.parse_args()
    
    # Load font
    print(f"Loading font...")
    font_obj = TTFont(args.input_ttf)
    
    # Check for vertical metrics tables
    if 'vmtx' in font_obj:
        print("Error: Font contains vmtx table, which is not supported", file=sys.stderr)
        return 1
    if 'vhea' in font_obj:
        print("Error: Font contains vhea table, which is not supported", file=sys.stderr)
        return 1
    
    # Parse glyph CSV
    print(f"Parsing glyph CSV...")
    glyphs_to_scale = set()
    with open(args.input_glyph_csv, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            glyph_index = int(row['glyph_index'])
            cmap_used = int(row['cmap_used'])
            glyf_used = int(row['glyf_used'])
            glyph_name = row['glyph_name']
            
            # Validate: if both cmap_used >= 1 and glyf_used >= 1, raise exception
            if cmap_used >= 1 and glyf_used >= 1:
                raise RuntimeError(
                    f"Glyph '{glyph_name}' (index {glyph_index}) has both "
                    f"cmap_used={cmap_used} and glyf_used={glyf_used}. "
                    f"Cannot scale glyphs used both in cmap and as components."
                )
            
            # If cmap_used >= 1, mark for scaling
            if cmap_used >= 1:
                glyphs_to_scale.add(glyph_index)
    
    print(f"Found {len(glyphs_to_scale)} glyphs to scale")
    
    # Get scale factor from arguments
    scale_factor = args.scale_factor
    print(f"Scale factor: {scale_factor:.6f}")
    
    # If widths match, just copy the file
    if abs(scale_factor - 1.0) < 0.0001:
        print("Scale factor is 1.0, copying file without scaling...")
        shutil.copy2(args.input_ttf, args.output_ttf)
        print(f"Copied to {args.output_ttf}")
        return 0
    
    # Scale the font
    print(f"Scaling font...")
    scaled_font = scale_font(font_obj, scale_factor, glyphs_to_scale)
    
    # Save the scaled font
    print(f"Saving scaled font to {args.output_ttf}...")
    scaled_font.save(args.output_ttf)
    print("Done!")
    
    return 0


if __name__ == '__main__':
    exit(main())
