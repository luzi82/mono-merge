#!/usr/bin/env python3
"""
mono-merge: A Python tool for merging monospace fonts
Merges English/Latin fonts with CJK fonts to create a unified monospace font
"""

import argparse
import sys
from pathlib import Path
from datetime import datetime
from collections import Counter
from fontTools.ttLib import TTFont
from fontTools.pens.ttGlyphPen import TTGlyphPen
from fontTools.pens.transformPen import TransformPen


def get_font_metrics(font):
    """
    Determine the dominant half-width and full-width of the font.
    Returns (half_width, full_width)
    """
    hmtx = font['hmtx']
    cmap = font.getBestCmap()
    
    # Try to find standard chars
    half_width = None
    full_width = None
    
    # Space (0x20) or 'A' (0x41) for half-width
    for cp in [0x20, 0x41]:
        if cp in cmap:
            half_width = hmtx[cmap[cp]][0]
            break
            
    # 'One' (0x4E00) or Ideographic Space (0x3000) for full-width
    for cp in [0x4E00, 0x3000]:
        if cp in cmap:
            full_width = hmtx[cmap[cp]][0]
            break
            
    # Fallback to statistics if needed
    if half_width is None or full_width is None:
        widths = [hmtx[name][0] for name in cmap.values()]
        if not widths:
            return 0, 0
        common = Counter(widths).most_common(2)
        sorted_widths = sorted([c[0] for c in common])
        
        if len(sorted_widths) == 1:
            # Only one width found?
            w = sorted_widths[0]
            # Guess based on UPM?
            upm = font['head'].unitsPerEm
            if abs(w - upm) < abs(w - upm/2):
                full_width = w
                half_width = w // 2
            else:
                half_width = w
                full_width = w * 2
        else:
            if half_width is None: half_width = sorted_widths[0]
            if full_width is None: full_width = sorted_widths[-1]
            
    return half_width, full_width


def get_latin_width(font):
    """Get the dominant width of the Latin font"""
    hmtx = font['hmtx']
    cmap = font.getBestCmap()
    
    # Try 'A'
    if 0x41 in cmap:
        return hmtx[cmap[0x41]][0]
        
    # Statistics
    widths = [hmtx[name][0] for name in cmap.values()]
    if not widths:
        return 1000 # Default
    return Counter(widths).most_common(1)[0][0]


def copy_glyph_from_latin(latin_font, cjk_font, latin_glyph_name, cjk_glyph_name, scale, glyphs_added_map, new_glyphs_list, y_offset=0):
    """
    Copy glyph from latin_font to cjk_font, scaling it.
    glyphs_added_map: maps latin_glyph_name -> new_cjk_glyph_name (for components)
    new_glyphs_list: list to append new component glyph names to (for glyphOrder)
    y_offset: vertical offset to apply to the glyph
    """
    if isinstance(latin_glyph_name, int):
        latin_glyph_name = latin_font.getGlyphName(latin_glyph_name)








    if latin_glyph_name in glyphs_added_map:
        return glyphs_added_map[latin_glyph_name]

    latin_glyf = latin_font['glyf']
    cjk_glyf = cjk_font['glyf']
    
    if latin_glyph_name not in latin_glyf:
        return None

    src_glyph = latin_glyf[latin_glyph_name]
    
    # If cjk_glyph_name is None, we are copying a component, so generate a new name
    is_component = cjk_glyph_name is None
    if is_component:
        cjk_glyph_name = f"cour_{latin_glyph_name}"
        # Ensure uniqueness
        while cjk_glyph_name in cjk_glyf or cjk_glyph_name in new_glyphs_list:
             cjk_glyph_name += "_"
        new_glyphs_list.append(cjk_glyph_name)
    
    # Record mapping before recursion to handle cycles
    glyphs_added_map[latin_glyph_name] = cjk_glyph_name
    
    if src_glyph.isComposite():
        pen = TTGlyphPen(cjk_glyf)
        for comp in src_glyph.components:
            # Recursively copy component
            new_comp_name = copy_glyph_from_latin(latin_font, cjk_font, comp.glyphName, None, scale, glyphs_added_map, new_glyphs_list, y_offset)




            
            if new_comp_name:
                # Scale transform
                xx, xy, yx, yy = 1, 0, 0, 1
                if hasattr(comp, 'transform'):
                    xx, xy = comp.transform[0]
                    yx, yy = comp.transform[1]
                dx, dy = comp.x, comp.y
                
                # Scale translation and apply y_offset
                dx = int(round(dx * scale))
                dy = int(round(dy * scale)) + y_offset
                
                pen.addComponent(new_comp_name, (xx, xy, yx, yy, dx, dy))
        
        cjk_glyf[cjk_glyph_name] = pen.glyph()
    else:
        # Simple glyph
        pen = TTGlyphPen(cjk_glyf)
        # Scale and apply y_offset
        transform_pen = TransformPen(pen, (scale, 0, 0, scale, 0, y_offset))
        src_glyph.draw(transform_pen, latin_glyf)
        cjk_glyf[cjk_glyph_name] = pen.glyph()
        
    # Update metrics for the new glyph
    if is_component:
        latin_hmtx = latin_font['hmtx']
        cjk_hmtx = cjk_font['hmtx']
        try:
            if latin_glyph_name in latin_hmtx:
                w, lsb = latin_hmtx[latin_glyph_name]
                cjk_hmtx[cjk_glyph_name] = (int(round(w * scale)), int(round(lsb * scale)))
            else:
                cjk_hmtx[cjk_glyph_name] = (0, 0)
        except Exception as e:
            print(f"ERROR accessing hmtx for {latin_glyph_name}: {e}", flush=True)
            cjk_hmtx[cjk_glyph_name] = (0, 0)


    return cjk_glyph_name


def apply_y_offset_to_glyphs(font, y_offset, exclude_glyphs=None):
    """
    Apply a vertical offset to all glyphs in the font.
    exclude_glyphs: set of glyph names to skip (e.g., Latin glyphs already processed)
    """
    if y_offset == 0:
        return
    
    if exclude_glyphs is None:
        exclude_glyphs = set()
    
    glyf_table = font['glyf']
    
    for glyph_name in font.getGlyphOrder():
        if glyph_name in exclude_glyphs or glyph_name not in glyf_table:
            continue
        
        glyph = glyf_table[glyph_name]
        
        if glyph.isComposite():
            # For composite glyphs, adjust component translations
            for comp in glyph.components:
                comp.y += y_offset
        elif glyph.numberOfContours > 0:
            # For simple glyphs, shift all coordinates
            for coord_list in [glyph.coordinates]:
                for i in range(len(coord_list)):
                    x, y = coord_list[i]
                    coord_list[i] = (x, y + y_offset)


def merge_fonts(latin_font_path, cjk_font_path, output_path, cjk_font_index=0, font_name=None, filter_chars=None, latin_y_offset=0, cjk_y_offset=0, font_ascender=None):
    print(f"Loading Latin font: {latin_font_path}")
    latin_font = TTFont(latin_font_path)
    
    # Check if CJK font is a TTC (collection) or single font (TTF/OTF)
    cjk_path_lower = str(cjk_font_path).lower()
    is_collection = cjk_path_lower.endswith('.ttc')
    is_otf = cjk_path_lower.endswith('.otf')
    
    if is_collection:
        print(f"Loading CJK font: {cjk_font_path} (index {cjk_font_index})")
        cjk_font = TTFont(cjk_font_path, fontNumber=cjk_font_index)
    else:
        print(f"Loading CJK font: {cjk_font_path}")
        cjk_font = TTFont(cjk_font_path)
    
    # Convert OTF (CFF-based) to TTF (glyf-based) if needed
    if is_otf and 'CFF ' in cjk_font:
        print("Converting OTF (CFF) to TTF (glyf) format...")
        # Use fontTools' cu2qu for proper CFF to TrueType conversion
        from fontTools.pens.cu2quPen import Cu2QuPen
        from fontTools.pens.ttGlyphPen import TTGlyphPen
        from fontTools.pens.recordingPen import RecordingPen
        
        # Get CFF data
        cff = cjk_font['CFF ']
        cff_dict = cff.cff[0]
        char_strings = cff_dict.CharStrings
        
        # Create glyf and loca tables
        from fontTools.ttLib.tables._g_l_y_f import table__g_l_y_f
        from fontTools.ttLib.tables._l_o_c_a import table__l_o_c_a
        
        glyf_table = table__g_l_y_f()
        glyf_table.glyphs = {}
        glyf_table.glyphOrder = cjk_font.getGlyphOrder()
        
        # Convert each glyph from CFF to glyf with cubic-to-quadratic conversion
        for glyph_name in glyf_table.glyphOrder:
            pen = TTGlyphPen(glyf_table.glyphs)
            if glyph_name in char_strings:
                t2_charstring = char_strings[glyph_name]
                # Use Cu2QuPen to convert cubic beziers to quadratic
                cu2qu_pen = Cu2QuPen(pen, 1.0, reverse_direction=False)
                try:
                    t2_charstring.draw(cu2qu_pen)
                except Exception as e:
                    # If conversion fails, create empty glyph
                    print(f"Warning: Failed to convert glyph '{glyph_name}': {e}")
                    pen = TTGlyphPen(glyf_table.glyphs)
            
            glyph = pen.glyph()
            glyph.recalcBounds(glyf_table.glyphs)
            glyf_table.glyphs[glyph_name] = glyph
        
        # Add glyf table to font
        cjk_font['glyf'] = glyf_table
        
        # Create loca table
        loca_table = table__l_o_c_a()
        cjk_font['loca'] = loca_table
        
        # Remove CFF table
        del cjk_font['CFF ']
        
        # Change sfntVersion from 'OTTO' (OpenType/CFF) to '\0\1\0\0' (TrueType)
        cjk_font.sfntVersion = '\0\1\0\0'
        
        # Update maxp table for TrueType
        if 'maxp' in cjk_font:
            maxp = cjk_font['maxp']
            maxp.tableVersion = 0x00010000
            # Initialize TrueType-specific maxp fields
            maxp.maxZones = 2
            maxp.maxTwilightPoints = 0
            maxp.maxStorage = 0
            maxp.maxFunctionDefs = 0
            maxp.maxInstructionDefs = 0
            maxp.maxStackElements = 0
            maxp.maxSizeOfInstructions = 0
            maxp.maxComponentElements = 0
            maxp.maxComponentDepth = 0
            # Recalculate maxp values from glyf table
            maxp.recalc(cjk_font)
        
        print("OTF to TTF conversion complete.")

    
    # 1. Detect char type (half-width/full-width) by CJK font
    print("Analyzing CJK metrics...")
    cjk_half_width, cjk_full_width = get_font_metrics(cjk_font)
    print(f"CJK Half Width: {cjk_half_width}")
    print(f"CJK Full Width: {cjk_full_width}")
    
    print("Analyzing Latin metrics...")
    latin_width = get_latin_width(latin_font)
    print(f"Latin Width: {latin_width}")
    
    # 3. The size of Latin font should be scaled
    scale = cjk_half_width / latin_width
    print(f"Scale Factor: {scale:.4f}")
    
    # Prepare for merge
    merged_font = cjk_font
    cjk_cmap = merged_font.getBestCmap()
    cjk_hmtx = merged_font['hmtx']
    latin_cmap = latin_font.getBestCmap()
    
    glyphs_added_map = {} # latin_name -> cjk_name
    new_component_glyphs = []
    
    print("Processing glyphs...")
    count_replaced = 0
    count_kept = 0
    
    # Iterate over all characters in CJK font
    for codepoint, glyph_name in cjk_cmap.items():
        if filter_chars and chr(codepoint) not in filter_chars:
            continue
            
        # Get current width
        current_width = cjk_hmtx[glyph_name][0]
        
        # 2. For half-width char, use Latin font, otherwise use CJK font
        # Check if it matches half-width (allow small tolerance)
        if abs(current_width - cjk_half_width) < 5:
            # It is half-width. Try to replace with Latin glyph.
            if codepoint in latin_cmap:
                latin_glyph_name = latin_cmap[codepoint]
                
                # Copy and scale glyph
                copy_glyph_from_latin(latin_font, merged_font, latin_glyph_name, glyph_name, scale, glyphs_added_map, new_component_glyphs, latin_y_offset)
                
                # Force width to be exactly cjk_half_width
                l_w, l_lsb = latin_font['hmtx'][latin_glyph_name]
                new_lsb = int(round(l_lsb * scale))
                cjk_hmtx[glyph_name] = (cjk_half_width, new_lsb)
                
                count_replaced += 1
            else:
                # Not in Latin font, keep CJK glyph but ensure width
                cjk_hmtx[glyph_name] = (cjk_half_width, cjk_hmtx[glyph_name][1])
                count_kept += 1
        
        elif abs(current_width - cjk_full_width) < 5:
            # Full width, keep CJK glyph, ensure width
            cjk_hmtx[glyph_name] = (cjk_full_width, cjk_hmtx[glyph_name][1])
            count_kept += 1
        else:
            # Other width? Keep as is.
            pass

    print(f"Replaced {count_replaced} half-width glyphs with Latin font.")
    print(f"Kept {count_kept} glyphs (full-width or missing in Latin).")
    
    # Apply CJK y-offset if specified
    if cjk_y_offset != 0:
        print(f"Applying CJK y-offset: {cjk_y_offset} units...")
        apply_y_offset_to_glyphs(merged_font, cjk_y_offset, exclude_glyphs=set(glyphs_added_map.values()) | set(new_component_glyphs))
    
    # Add new component glyphs to glyphOrder
    if new_component_glyphs:
        print(f"Adding {len(new_component_glyphs)} new component glyphs...")
        glyph_order = merged_font.getGlyphOrder()
        merged_font.setGlyphOrder(glyph_order + new_component_glyphs)

    # Remove DSIG
    if 'DSIG' in merged_font:
        del merged_font['DSIG']

    # Update Name Table
    if font_name:
        print(f"Setting font name to: {font_name}")
        name_table = merged_font['name']
        family_name = font_name
        subfamily_name = 'Regular'
        full_name = f"{font_name} {subfamily_name}".strip()
        unique_name = f"{font_name} {datetime.now().strftime('%Y%m%d')}"
        ps_name = ''.join(ch for ch in font_name if ch.isalnum()) or 'MonoMerged'

        def set_name_all_platforms(name_id, value):
            if value is None: return
            name_table.setName(value, name_id, 3, 1, 0x409)
            name_table.setName(value, name_id, 1, 0, 0)
            name_table.setName(value, name_id, 0, 3, 0)

        name_ids_to_clean = {1, 2, 3, 4, 6, 16, 17, 21, 22}
        name_table.names = [r for r in name_table.names if r.nameID not in name_ids_to_clean]

        set_name_all_platforms(1, family_name)
        set_name_all_platforms(2, subfamily_name)
        set_name_all_platforms(3, unique_name)
        set_name_all_platforms(4, full_name)
        set_name_all_platforms(6, ps_name)

    # Set font ascender if specified
    if font_ascender is not None:
        print(f"Setting font ascender to: {font_ascender}")
        # Update hhea table
        if 'hhea' in merged_font:
            merged_font['hhea'].ascent = font_ascender
        # Update OS/2 table
        if 'OS/2' in merged_font:
            merged_font['OS/2'].sTypoAscender = font_ascender
            merged_font['OS/2'].usWinAscent = font_ascender

    # Ensure glyphOrder matches glyf table to prevent AssertionError
    if 'glyf' in merged_font:
        glyf_table = merged_font['glyf']
        glyf_keys = set(glyf_table.keys())
        current_order = merged_font.getGlyphOrder()
        
        # Filter out glyphs from order that are not in glyf table, and remove duplicates
        seen = set()
        final_order = []
        for g in current_order:
            if g in glyf_keys and g not in seen:
                final_order.append(g)
                seen.add(g)
        
        # Add any glyphs in glyf table that are missing from order
        missing_glyphs = [g for g in glyf_keys if g not in seen]
        
        if missing_glyphs:
            print(f"Warning: {len(missing_glyphs)} glyphs were in glyf table but not in glyphOrder. Adding them.")
            final_order.extend(sorted(missing_glyphs))
            
        merged_font.setGlyphOrder(final_order)

    # Save the merged font
    print(f"Saving merged font to: {output_path}")
    merged_font.save(output_path, reorderTables=True)
    print("Done!")
    
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
  %(prog)s -l input/consola.ttf -c input/NotoSansMonoCJKhk-Regular.otf
  %(prog)s -l input/consola.ttf -c input/NotoSansMonoCJKhk-Regular.otf -n MyCustomFont
  %(prog)s -l input/consola.ttf -c input/NotoSansMonoCJKhk-Regular.otf -o output/custom.ttf -i 1
        """
    )
    
    parser.add_argument(
        '-l', '--latin-font',
        type=str,
        default='input/consola.ttf',
        help='Path to the Latin/English font file (default: input/consola.ttf)'
    )
    
    parser.add_argument(
        '-c', '--cjk-font',
        type=str,
        default='input/NotoSansMonoCJKhk-Regular.otf',
        help='Path to the CJK font file (supports TTC, TTF, and OTF formats; default: input/NotoSansMonoCJKhk-Regular.otf)'
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
        default=0,
        help='Font index in TTC file (default: 0). Only applies to TTC files; ignored for TTF/OTF.'
    )

    parser.add_argument(
        '--char',
        type=str,
        help='Specific characters to include from CJK font (for debugging/testing)'
    )

    parser.add_argument(
        '--latin-y-offset',
        type=int,
        default=0,
        help='Vertical offset (in font units) to apply to Latin glyphs (default: 0)'
    )

    parser.add_argument(
        '--cjk-y-offset',
        type=int,
        default=0,
        help='Vertical offset (in font units) to apply to CJK glyphs (default: 0)'
    )

    parser.add_argument(
        '--font-ascender',
        type=int,
        help='Hard code the font ascender value in font units (sets both hhea and OS/2 tables)'
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
        filter_chars=args.char,
        latin_y_offset=args.latin_y_offset,
        cjk_y_offset=args.cjk_y_offset,
        font_ascender=args.font_ascender
    )
    
    return 0 if success else 1


if __name__ == '__main__':
    sys.exit(main())
