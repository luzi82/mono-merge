#!/usr/bin/env python3
"""
mono-merge: A Python tool for merging monospace fonts
Merges English/Latin fonts with CJK fonts to create a unified monospace font
"""

import argparse
import sys
from pathlib import Path
from datetime import datetime
from fontTools.ttLib import TTFont
from fontTools.pens.t2CharStringPen import T2CharStringPen
from fontTools.pens.ttGlyphPen import TTGlyphPen
from fontTools.pens.transformPen import TransformPen


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


def merge_fonts(latin_font_path, cjk_font_path, output_path, cjk_font_index=0, font_name=None, filter_chars=None):
    """
    Merge Latin and CJK fonts into a single monospace font
    
    Args:
        latin_font_path: Path to the Latin/English font (e.g., cour.ttf)
        cjk_font_path: Path to the CJK font (e.g., mingliu.ttc)
        output_path: Path for the output merged font
        cjk_font_index: Index of font in TTC file (0 for MingLiU, 1 for MingLiU_HKSCS, etc.)
        font_name: Name for the merged font (default: None, keeps original name)
        filter_chars: String of characters to include from CJK font. If None, include all CJK chars.
    """
    print(f"Loading Latin font: {latin_font_path}")
    latin_font = TTFont(latin_font_path)
    
    print(f"Loading CJK font: {cjk_font_path} (index {cjk_font_index})")
    cjk_font = TTFont(cjk_font_path, fontNumber=cjk_font_index)
    
    # Get font metrics to determine target widths
    # For monospace fonts, we want half-width:height = 1:2, full-width:height = 1:1
    
    # Get UPM (units per em) from the Latin font
    upm = latin_font['head'].unitsPerEm
    cjk_upm = cjk_font['head'].unitsPerEm
    scale_factor = upm / cjk_upm
    
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
    latin_cmap = latin_font.getBestCmap().copy()
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
    
    # Identify all glyphs to copy (including components)
    glyphs_to_copy = set()
    
    # First, find all CJK glyphs from cmap
    for codepoint, cjk_glyph_name in cjk_cmap.items():
        if is_cjk_char(codepoint):
            # If filter_chars is provided, only include characters in the filter
            if filter_chars is not None and chr(codepoint) not in filter_chars:
                continue
                
            if isinstance(cjk_glyph_name, int):
                cjk_glyph_name = f"glyph{cjk_glyph_name:05d}"
            glyphs_to_copy.add(cjk_glyph_name)
            # Update cmap immediately
            latin_cmap[codepoint] = cjk_glyph_name

    # Recursively find components
    # We need to check if any glyph in glyphs_to_copy is composite
    # and if so, add its components to the set
    
    print(f"Initial CJK glyphs to copy: {len(glyphs_to_copy)}")
    
    processed_glyphs = set()
    while True:
        new_glyphs = set()
        for glyph_name in glyphs_to_copy:
            if glyph_name in processed_glyphs:
                continue
            
            processed_glyphs.add(glyph_name)
            
            # Check if glyph exists in CJK font
            if glyph_name in cjk_glyf_table:
                glyph = cjk_glyf_table[glyph_name]
                if glyph.isComposite():
                    for component in glyph.components:
                        comp_name = component.glyphName
                        if comp_name not in glyphs_to_copy and comp_name not in new_glyphs:
                            new_glyphs.add(comp_name)
        
        if not new_glyphs:
            break
            
        print(f"Found {len(new_glyphs)} component glyphs to add...")
        glyphs_to_copy.update(new_glyphs)

    print(f"Total glyphs to copy (including components): {len(glyphs_to_copy)}")

    # Now copy all identified glyphs
    glyphs_added = 0
    successful_glyphs = set()
    for cjk_glyph_name in glyphs_to_copy:
        try:
            # Check if glyph exists in CJK font
            if glyf_table and cjk_glyf_table and cjk_glyph_name in cjk_glyf_table:
                # Copy the glyph
                src_glyph = cjk_glyf_table[cjk_glyph_name]
                
                if scale_factor != 1.0:
                    if src_glyph.isComposite():
                        # For composite glyphs, we only scale the offset (translation)
                        # We do NOT scale the component itself because the component glyph 
                        # will be scaled when it is copied (or already has been).
                        pen = TTGlyphPen(glyf_table)
                        for comp in src_glyph.components:
                            # Get original transform
                            xx, xy, yx, yy = 1, 0, 0, 1
                            if hasattr(comp, 'transform'):
                                xx, xy = comp.transform[0]
                                yx, yy = comp.transform[1]
                            dx, dy = comp.x, comp.y
                            
                            # Scale translation
                            dx = int(round(dx * scale_factor))
                            dy = int(round(dy * scale_factor))
                            
                            # Add component with new transform
                            pen.addComponent(comp.glyphName, (xx, xy, yx, yy, dx, dy))
                        
                        glyf_table[cjk_glyph_name] = pen.glyph()
                    else:
                        # For simple glyphs, we scale the coordinates
                        pen = TTGlyphPen(glyf_table)
                        transform_pen = TransformPen(pen, (scale_factor, 0, 0, scale_factor, 0, 0))
                        src_glyph.draw(transform_pen, cjk_glyf_table)
                        new_glyph = pen.glyph()
                        glyf_table[cjk_glyph_name] = new_glyph
                else:
                    glyf_table[cjk_glyph_name] = src_glyph
                
                # Recalculate bounds for the new glyph (simple or composite)
                if scale_factor != 1.0:
                     glyf_table[cjk_glyph_name].recalcBounds(glyf_table)
                
                # Copy the metrics
                try:
                    hmtx_table[cjk_glyph_name] = cjk_hmtx_table[cjk_glyph_name]
                except KeyError:
                    # Glyph might not have metrics if it's just a component? 
                    # Usually all glyphs have hmtx. Use default if missing.
                    hmtx_table[cjk_glyph_name] = (target_full_width, 0)
                
                glyphs_added += 1
                successful_glyphs.add(cjk_glyph_name)
        except (KeyError, Exception) as e:
            # Skip glyphs that can't be copied
            print(f"Warning: Failed to copy glyph {cjk_glyph_name}: {e}")
            continue
    
    print(f"Successfully added {glyphs_added} glyphs")
    
    # Explicitly update glyphOrder to ensure cmap compiles correctly
    if glyphs_added > 0:
        print("Updating glyphOrder...")
        current_order = merged_font.getGlyphOrder()
        existing_set = set(current_order)
        # Find glyphs that are in successful_glyphs but not in current_order
        new_glyphs_list = [g for g in successful_glyphs if g not in existing_set]
        # Sort for determinism
        new_glyphs_list.sort()
        
        if new_glyphs_list:
            new_order = current_order + new_glyphs_list
            merged_font.setGlyphOrder(new_order)
            print(f"Added {len(new_glyphs_list)} glyphs to glyphOrder")
            
    # Clean up cmap - remove entries pointing to failed glyphs
    failed_glyphs = glyphs_to_copy - successful_glyphs
    if failed_glyphs:
        print(f"Removing {len(failed_glyphs)} failed glyphs from cmap...")
        # Create a list of keys to remove to avoid runtime error during iteration
        keys_to_remove = [cp for cp, name in latin_cmap.items() if name in failed_glyphs]
        for cp in keys_to_remove:
            del latin_cmap[cp]

    # Remove DSIG table if present to avoid signature validation errors
    if 'DSIG' in merged_font:
        print("Removing DSIG table...")
        del merged_font['DSIG']
    
    # Update OS/2 table to include CJK Unicode ranges
    if 'OS/2' in merged_font:
        print("Updating OS/2 table for CJK support...")
        os2_table = merged_font['OS/2']
        
        # Update Unicode range bits (ulUnicodeRange1-4)
        # Bit 59: CJK Unified Ideographs (4E00-9FFF)
        # Bit 60: Private Use Area (E000-F8FF)
        # Bit 61: CJK Compatibility Ideographs (F900-FAFF)
        
        # ulUnicodeRange2 bits (32-63)
        # Set bit 59 (CJK Unified Ideographs) - bit 27 of ulUnicodeRange2
        os2_table.ulUnicodeRange2 |= (1 << 27)  # Bit 59: CJK Unified Ideographs
        os2_table.ulUnicodeRange2 |= (1 << 29)  # Bit 61: CJK Compatibility Ideographs
        
        # ulUnicodeRange3 bits (64-95)
        # Set bit 64 (Hiragana), bit 65 (Katakana)
        os2_table.ulUnicodeRange3 |= (1 << 0)   # Bit 64: Hiragana
        os2_table.ulUnicodeRange3 |= (1 << 1)   # Bit 65: Katakana
        os2_table.ulUnicodeRange3 |= (1 << 4)   # Bit 68: Hangul Syllables
        
        # Update codepage range for Chinese support
        # Bit 17: Chinese: Simplified chars (PRC and Singapore)
        # Bit 18: Chinese: Traditional chars (Taiwan and Hong Kong)
        os2_table.ulCodePageRange1 |= (1 << 17)  # Simplified Chinese
        os2_table.ulCodePageRange1 |= (1 << 18)  # Traditional Chinese
    
    # Update the cmap table
    # Create new cmap tables to ensure they are clean and contain all mappings
    from fontTools.ttLib.tables._c_m_a_p import CmapSubtable
    
    # Windows Unicode BMP (Platform 3, Encoding 1, Format 4)
    cmap_win = CmapSubtable.newSubtable(4)
    cmap_win.platformID = 3
    cmap_win.platEncID = 1
    cmap_win.language = 0
    cmap_win.cmap = latin_cmap
    
    # Unicode BMP (Platform 0, Encoding 3, Format 4)
    cmap_uni = CmapSubtable.newSubtable(4)
    cmap_uni.platformID = 0
    cmap_uni.platEncID = 3
    cmap_uni.language = 0
    cmap_uni.cmap = latin_cmap
    
    merged_font['cmap'].tables = [cmap_win, cmap_uni]
    
    # Update font name if provided
    if font_name:
        print(f"Setting font name to: {font_name}")
        name_table = merged_font['name']

        # Prepare consistent naming components
        family_name = font_name
        subfamily_name = 'Regular'
        full_name = f"{font_name} {subfamily_name}".strip()
        unique_name = f"{font_name} {datetime.now().strftime('%Y%m%d')}"
        ps_name = ''.join(ch for ch in font_name if ch.isalnum()) or 'MonoMerged'

        # Helper for writing all platform/encoding combos Windows and macOS expect
        def set_name_all_platforms(name_id, value):
            if value is None:
                return
            name_table.setName(value, name_id, 3, 1, 0x409)  # Windows, Unicode BMP, en-US
            name_table.setName(value, name_id, 1, 0, 0)      # macOS, Roman, English
            name_table.setName(value, name_id, 0, 3, 0)      # Unicode, BMP

        # Remove any stale name records likely to confuse Windows viewers
        # Also remove WWS names (21, 22) if present
        name_ids_to_clean = {1, 2, 3, 4, 6, 16, 17, 21, 22}
        name_table.names = [
            record for record in name_table.names if record.nameID not in name_ids_to_clean
        ]

        # Populate the critical name records
        set_name_all_platforms(1, family_name)      # Font Family name
        set_name_all_platforms(2, subfamily_name)   # Font Subfamily (Regular)
        set_name_all_platforms(3, unique_name)      # Unique identifier
        set_name_all_platforms(4, full_name)        # Full font name
        set_name_all_platforms(6, ps_name)          # PostScript name (no spaces)
        set_name_all_platforms(16, family_name)     # Typographic family name
        set_name_all_platforms(17, subfamily_name)  # Typographic subfamily name
    
    # Save the merged font
    print(f"Saving merged font to: {output_path}")
    merged_font.save(output_path)
    
    print("Font merge completed successfully!")
    return True


def main():
    # Generate default font name with timestamp
    today = datetime.now().strftime('%Y%m%d%H%M%S')
    default_output = f'output/mono_{today}.ttf'
    
    parser = argparse.ArgumentParser(
        description='Merge monospace fonts for English and CJK characters',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s -l input/cour.ttf -c input/mingliu.ttc
  %(prog)s -l input/cour.ttf -c input/mingliu.ttc -n MyCustomFont
  %(prog)s -l input/cour.ttf -c input/mingliu.ttc -o output/custom.ttf -i 1
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
        '-n', '--name',
        type=str,
        help='Output font name (default: mono_YYYYMMDDHHMMSS). Used to generate output filename.'
    )
    
    parser.add_argument(
        '-o', '--output',
        type=str,
        help=f'Path for the output merged font (default: {default_output})'
    )
    
    parser.add_argument(
        '-i', '--cjk-index',
        type=int,
        default=2,
        help='Font index in TTC file (0=MingLiU, 1=PMingLiU, 2=MingLiU_HKSCS, 3=MingLiU_MSCS, default: 2)'
    )

    parser.add_argument(
        '--char',
        type=str,
        help='Specific characters to include from CJK font (for debugging/testing)'
    )
    
    args = parser.parse_args()
    
    # Determine output path
    if args.output:
        output_path = Path(args.output)
    elif args.name:
        output_path = Path(f'output/{args.name}.ttf')
    else:
        output_path = Path(default_output)
    
    # Determine font name (for internal font metadata)
    if args.name:
        font_name = args.name
    else:
        font_name = f"mono {today}"
    
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
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Merge fonts
    success = merge_fonts(
        str(latin_path),
        str(cjk_path),
        str(output_path),
        args.cjk_index,
        font_name,
        filter_chars=args.char
    )
    
    return 0 if success else 1


if __name__ == '__main__':
    sys.exit(main())
