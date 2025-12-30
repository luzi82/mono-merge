#!/usr/bin/env python3
"""
Scale a font to match the advance width of another font.
"""

import argparse
import shutil
from fontTools.ttLib import TTFont


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


def scale_font(font, scale_factor):
    """
    Scale a font by a given factor.
    
    Args:
        font: TTFont object
        scale_factor: Scaling factor (e.g., 1.2 for 120%)
        
    Returns:
        Modified TTFont object
    """
    # Scale glyph coordinates
    if 'glyf' in font:
        glyf_table = font['glyf']
        for glyph_name in font.getGlyphOrder():
            if glyph_name not in glyf_table:
                continue
            
            glyph = glyf_table[glyph_name]
            
            if glyph.isComposite():
                # For composite glyphs, scale component translations
                for comp in glyph.components:
                    comp.x = int(comp.x * scale_factor)
                    comp.y = int(comp.y * scale_factor)
                    # Scale component transform if present
                    if hasattr(comp, 'transform'):
                        transform = comp.transform
                        comp.transform = (
                            transform[0],  # xx - keep scale
                            transform[1],  # xy - keep skew
                            transform[2],  # yx - keep skew
                            transform[3],  # yy - keep scale
                            int(transform[4] * scale_factor),  # dx - scale translation
                            int(transform[5] * scale_factor)   # dy - scale translation
                        )
            elif glyph.numberOfContours > 0:
                # For simple glyphs, scale all coordinates
                coords = glyph.coordinates
                for i in range(len(coords)):
                    x, y = coords[i]
                    coords[i] = (int(x * scale_factor), int(y * scale_factor))
    
    # Scale horizontal metrics (advance widths and left side bearings)
    if 'hmtx' in font:
        hmtx = font['hmtx']
        for glyph_name in font.getGlyphOrder():
            try:
                advance_width, lsb = hmtx[glyph_name]
                hmtx[glyph_name] = (int(advance_width * scale_factor), int(lsb * scale_factor))
            except KeyError:
                pass
    
    # Scale vertical metrics if present
    if 'vmtx' in font:
        vmtx = font['vmtx']
        for glyph_name in font.getGlyphOrder():
            try:
                advance_height, tsb = vmtx[glyph_name]
                vmtx[glyph_name] = (int(advance_height * scale_factor), int(tsb * scale_factor))
            except KeyError:
                pass
    
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
    
    # Scale vhea table if present
    if 'vhea' in font:
        vhea = font['vhea']
        vhea.ascent = int(vhea.ascent * scale_factor)
        vhea.descent = int(vhea.descent * scale_factor)
        vhea.lineGap = int(vhea.lineGap * scale_factor)
        vhea.advanceHeightMax = int(vhea.advanceHeightMax * scale_factor)
        vhea.minTopSideBearing = int(vhea.minTopSideBearing * scale_factor)
        vhea.minBottomSideBearing = int(vhea.minBottomSideBearing * scale_factor)
        vhea.yMaxExtent = int(vhea.yMaxExtent * scale_factor)
    
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
        'input_scale_ttf',
        help='The TTF font to be scaled'
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
    scale_font_obj = TTFont(args.input_scale_ttf)
    
    # Get scale factor from arguments
    scale_factor = args.scale_factor
    print(f"Scale factor: {scale_factor:.6f}")
    
    # If widths match, just copy the file
    if abs(scale_factor - 1.0) < 0.0001:
        print("Widths match, copying file without scaling...")
        shutil.copy2(args.input_scale_ttf, args.output_ttf)
        print(f"Copied to {args.output_ttf}")
        return 0
    
    # Scale the font
    print(f"Scaling font...")
    scaled_font = scale_font(scale_font_obj, scale_factor)
    
    # Save the scaled font
    print(f"Saving scaled font to {args.output_ttf}...")
    scaled_font.save(args.output_ttf)
    print("Done!")
    
    return 0


if __name__ == '__main__':
    exit(main())
