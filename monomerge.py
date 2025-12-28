#!/usr/bin/env python3
"""
mono-merge: A Python tool for merging monospace fonts
Merges English/Latin fonts with CJK fonts to create a unified monospace font
"""

import argparse
import sys
from pathlib import Path
from fontTools.ttLib import TTFont
from fontTools.pens.t2CharStringPen import T2CharStringPen
from fontTools.pens.ttGlyphPen import TTGlyphPen


def get_glyph_width(font, glyph_name):
    """Get the advance width of a glyph"""
    if 'hmtx' in font:
        return font['hmtx'][glyph_name][0]
    return 0


def set_glyph_width(font, glyph_name, width):
    """Set the advance width of a glyph"""
    if 'hmtx' in font:
        advance_width, lsb = font['hmtx'][glyph_name]
        font['hmtx'][glyph_name] = (width, lsb)


def is_cjk_char(codepoint):
    """Check if a Unicode codepoint is a CJK character or full-width character"""
    # CJK Unified Ideographs
    if 0x4E00 <= codepoint <= 0x9FFF:
        return True
    # CJK Unified Ideographs Extension A
    if 0x3400 <= codepoint <= 0x4DBF:
        return True
    # CJK Unified Ideographs Extension B-F
    if 0x20000 <= codepoint <= 0x2EBEF:
        return True
    # CJK Compatibility Ideographs
    if 0xF900 <= codepoint <= 0xFAFF:
        return True
    if 0x2F800 <= codepoint <= 0x2FA1F:
        return True
    # Hangul Syllables (Korean)
    if 0xAC00 <= codepoint <= 0xD7AF:
        return True
    # Hiragana and Katakana
    if 0x3040 <= codepoint <= 0x30FF:
        return True
    # Katakana Phonetic Extensions
    if 0x31F0 <= codepoint <= 0x31FF:
        return True
    # CJK Symbols and Punctuation (full-width)
    if 0x3000 <= codepoint <= 0x303F:
        return True
    # Full-width ASCII variants
    if 0xFF00 <= codepoint <= 0xFFEF:
        return True
    # Enclosed CJK Letters and Months
    if 0x3200 <= codepoint <= 0x32FF:
        return True
    # CJK Compatibility
    if 0x3300 <= codepoint <= 0x33FF:
        return True
    return False


def standardize_font_widths(font, target_half_width, target_full_width, is_cjk_font=False):
    """
    Standardize glyph widths in a font
    target_half_width: target width for half-width characters
    target_full_width: target width for full-width characters
    is_cjk_font: if True, most glyphs should be full-width
    """
    cmap = font.getBestCmap()
    if not cmap:
        return
    
    for codepoint, glyph_name in cmap.items():
        if is_cjk_char(codepoint):
            # CJK and full-width characters
            set_glyph_width(font, glyph_name, target_full_width)
        else:
            # Half-width characters (ASCII, etc.)
            set_glyph_width(font, glyph_name, target_half_width)


def merge_fonts(latin_font_path, cjk_font_path, output_path, cjk_font_index=0):
    """
    Merge Latin and CJK fonts into a single monospace font
    
    Args:
        latin_font_path: Path to the Latin/English font (e.g., cour.ttf)
        cjk_font_path: Path to the CJK font (e.g., mingliu.ttc)
        output_path: Path for the output merged font
        cjk_font_index: Index of font in TTC file (0 for MingLiU, 1 for MingLiU_HKSCS, etc.)
    """
    print(f"Loading Latin font: {latin_font_path}")
    latin_font = TTFont(latin_font_path)
    
    print(f"Loading CJK font: {cjk_font_path} (index {cjk_font_index})")
    cjk_font = TTFont(cjk_font_path, fontNumber=cjk_font_index)
    
    # Get font metrics to determine target widths
    # For monospace fonts, we want half-width:height = 1:2, full-width:height = 1:1
    
    # Get UPM (units per em) from the Latin font
    upm = latin_font['head'].unitsPerEm
    
    # Calculate target widths based on the font's em height
    # For proper monospace: half-width should be upm/2, full-width should be upm
    target_half_width = upm // 2
    target_full_width = upm
    
    print(f"Font UPM: {upm}")
    print(f"Target half-width: {target_half_width}")
    print(f"Target full-width: {target_full_width}")
    
    # Standardize widths in both fonts
    print("Standardizing Latin font widths...")
    standardize_font_widths(latin_font, target_half_width, target_full_width, is_cjk_font=False)
    
    print("Standardizing CJK font widths...")
    standardize_font_widths(cjk_font, target_half_width, target_full_width, is_cjk_font=True)
    
    # Start with the Latin font as base
    merged_font = latin_font
    
    # Get character maps
    latin_cmap = latin_font.getBestCmap()
    cjk_cmap = cjk_font.getBestCmap()
    
    if not latin_cmap or not cjk_cmap:
        print("Error: Could not get character maps from fonts")
        return False
    
    # Copy CJK glyphs to the merged font
    print("Merging CJK glyphs...")
    glyf_table = merged_font.get('glyf')
    cjk_glyf_table = cjk_font.get('glyf')
    
    # Copy metrics table data
    hmtx_table = merged_font['hmtx']
    cjk_hmtx_table = cjk_font['hmtx']
    
    glyphs_added = 0
    for codepoint, cjk_glyph_name in cjk_cmap.items():
        if is_cjk_char(codepoint):
            # This is a CJK character, use the glyph from CJK font
            # Convert glyph name to string if it's not already
            if isinstance(cjk_glyph_name, int):
                cjk_glyph_name = f"glyph{cjk_glyph_name:05d}"
            
            try:
                # Check if glyph exists in CJK font
                if glyf_table and cjk_glyf_table and cjk_glyph_name in cjk_glyf_table:
                    # Copy the glyph
                    glyf_table[cjk_glyph_name] = cjk_glyf_table[cjk_glyph_name]
                    
                    # Copy the metrics
                    try:
                        hmtx_table[cjk_glyph_name] = cjk_hmtx_table[cjk_glyph_name]
                    except KeyError:
                        # Glyph doesn't have metrics, skip it
                        continue
                    
                    # Update the cmap to point to this glyph
                    latin_cmap[codepoint] = cjk_glyph_name
                    glyphs_added += 1
            except (KeyError, Exception) as e:
                # Skip glyphs that can't be copied
                continue
    
    print(f"Added {glyphs_added} CJK glyphs")
    
    # Update the cmap table
    for table in merged_font['cmap'].tables:
        if table.isUnicode():
            table.cmap = latin_cmap
    
    # Save the merged font
    print(f"Saving merged font to: {output_path}")
    merged_font.save(output_path)
    
    print("Font merge completed successfully!")
    return True


def main():
    parser = argparse.ArgumentParser(
        description='Merge monospace fonts for English and CJK characters',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s -l input/cour.ttf -c input/mingliu.ttc -o output/merged.ttf
  %(prog)s -l input/cour.ttf -c input/mingliu.ttc -o output/merged.ttf -i 1
        """
    )
    
    parser.add_argument(
        '-l', '--latin-font',
        type=str,
        default='input/cour.ttf',
        help='Path to the Latin/English font file (default: input/cour.ttf)'
    )
    
    parser.add_argument(
        '-c', '--cjk-font',
        type=str,
        default='input/mingliu.ttc',
        help='Path to the CJK font file (default: input/mingliu.ttc)'
    )
    
    parser.add_argument(
        '-o', '--output',
        type=str,
        default='output/merged.ttf',
        help='Path for the output merged font (default: output/merged.ttf)'
    )
    
    parser.add_argument(
        '-i', '--cjk-index',
        type=int,
        default=1,
        help='Font index in TTC file (0=MingLiU, 1=MingLiU_HKSCS, default: 1)'
    )
    
    args = parser.parse_args()
    
    # Validate input files
    latin_path = Path(args.latin_font)
    cjk_path = Path(args.cjk_font)
    
    if not latin_path.exists():
        print(f"Error: Latin font file not found: {latin_path}", file=sys.stderr)
        return 1
    
    if not cjk_path.exists():
        print(f"Error: CJK font file not found: {cjk_path}", file=sys.stderr)
        return 1
    
    # Create output directory if it doesn't exist
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Merge fonts
    success = merge_fonts(
        str(latin_path),
        str(cjk_path),
        str(output_path),
        args.cjk_index
    )
    
    return 0 if success else 1


if __name__ == '__main__':
    sys.exit(main())
