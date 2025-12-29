#!/usr/bin/env python3
"""
Merge multiple TTF font files based on a pick CSV file and metadata YAML.
Creates a new monospace font by combining glyphs from base and multiple source fonts.
"""

import argparse
import csv
import sys
import yaml
from pathlib import Path
from datetime import datetime
from fontTools.ttLib import TTFont
from fontTools.ttLib.tables._g_a_s_p import table__g_a_s_p, GASP_SYMMETRIC_GRIDFIT, GASP_SYMMETRIC_SMOOTHING, GASP_DOGRAY, GASP_GRIDFIT


def merge_fonts(input_base_ttf, input_ttf_list, input_pick_csv, input_meta_yaml, output_ttf, font_name, vendor_id):
    """
    Merge multiple TTF fonts based on pick CSV and metadata YAML.
    
    Args:
        input_base_ttf: Path to base TTF font file
        input_ttf_list: List of paths to TTF font files to merge
        input_pick_csv: Path to pick CSV file (from pick_font.py)
        input_meta_yaml: Path to metadata YAML file (from cal_meta.py)
        output_ttf: Path for output merged TTF file
        font_name: Name for the output font
        vendor_id: OS/2 vendor ID (4 characters)
    """
    print(f"Loading base font: {input_base_ttf}")
    base_font = TTFont(input_base_ttf)
    
    # Load all source fonts
    source_fonts = []
    for font_path in input_ttf_list:
        print(f"Loading source font: {font_path}")
        source_fonts.append(TTFont(font_path))
    
    print(f"Loading pick CSV: {input_pick_csv}")
    with open(input_pick_csv, 'r', encoding='utf-8') as f:
        pick_reader = csv.DictReader(f)
        pick_data = {int(row['codepoint_dec']): row for row in pick_reader}
    
    print(f"Loading metadata: {input_meta_yaml}")
    with open(input_meta_yaml, 'r', encoding='utf-8') as f:
        metadata = yaml.safe_load(f)
    
    half_advance_width = metadata['half_advance_width']
    full_advance_width = metadata['full_advance_width']
    ascender = metadata['ascender']
    descender = metadata['descender']
    
    print(f"Metadata: half_width={half_advance_width}, full_width={full_advance_width}")
    print(f"Metadata: ascender={ascender}, descender={descender}")
    
    # Get cmap, hmtx, and glyf from base font and all source fonts BEFORE modifying
    base_cmap = base_font.getBestCmap()
    base_hmtx = base_font['hmtx']
    base_glyf = base_font['glyf']
    
    source_cmaps = [font.getBestCmap() for font in source_fonts]
    source_hmtxs = [font['hmtx'] for font in source_fonts]
    source_glyfs = [font['glyf'] for font in source_fonts]
    
    # Reuse base font and replace character data in it
    print("Creating merged font from base font...")
    merged_font = base_font

    # Remove GSUB and GPOS tables to avoid "Bad ligature glyph" errors
    # since we are changing glyph indices and names
    # Also remove variable font tables and other unnecessary tables
    tables_to_remove = [
        'GSUB', 'GPOS', 'DSIG', 'HVAR', 'VVAR', 'STAT', 'avar', 
        'fvar', 'gvar', 'cvar', 'MVAR'
    ]
    for table_tag in tables_to_remove:
        if table_tag in merged_font:
            print(f"Removing {table_tag} table...")
            del merged_font[table_tag]
            
    # Remove format 14 cmap subtables (Unicode Variation Sequences)
    # as they are likely invalid after glyph pruning/renaming
    if 'cmap' in merged_font:
        cmap_table = merged_font['cmap']
        new_tables = []
        for subtable in cmap_table.tables:
            if subtable.format == 14:
                print("Removing cmap format 14 subtable...")
                continue
            new_tables.append(subtable)
        cmap_table.tables = new_tables

    # Prune unused glyphs to free up space (especially if base font is full)
    if 'glyf' in merged_font:
        print("Pruning unused glyphs...")
        cmap = merged_font.getBestCmap()
        glyf = merged_font['glyf']
        hmtx = merged_font['hmtx']
        
        # Start with mapped glyphs and .notdef
        used_glyphs = set(cmap.values())
        if '.notdef' in glyf:
            used_glyphs.add('.notdef')
            
        # Expand to include components
        stack = list(used_glyphs)
        while stack:
            gname = stack.pop()
            if gname in glyf:
                glyph = glyf[gname]
                if glyph.isComposite():
                    for comp in glyph.components:
                        if comp.glyphName not in used_glyphs:
                            used_glyphs.add(comp.glyphName)
                            stack.append(comp.glyphName)
                            
        # Remove unused
        all_glyphs = merged_font.getGlyphOrder()
        new_glyph_order = [g for g in all_glyphs if g in used_glyphs]
        
        print(f"Pruning glyphs: {len(all_glyphs)} -> {len(new_glyph_order)}")
        
        merged_font.setGlyphOrder(new_glyph_order)
        merged_font['maxp'].numGlyphs = len(new_glyph_order)
        
        # Clean up hmtx table and glyf table
        # We must manually remove glyphs from the internal dictionary to avoid
        # triggering the automatic glyphOrder update (which would fail since we already updated it)
        # and to ensure the glyphs dictionary matches the new glyphOrder (to avoid AssertionError at save)
        for g in all_glyphs:
            if g not in used_glyphs:
                if g in hmtx.metrics:
                    del hmtx.metrics[g]
                if g in glyf.glyphs:
                    del glyf.glyphs[g]

    # Merge OS/2 code page and unicode ranges from all source fonts to ensure compatibility
    if 'OS/2' in merged_font:
        print("Merging OS/2 CodePage and Unicode ranges...")
        base_os2 = merged_font['OS/2']
        
        # Helper to merge attributes safely
        def merge_attr(attr, src_os2):
            if hasattr(base_os2, attr) and hasattr(src_os2, attr):
                val_base = getattr(base_os2, attr)
                val_src = getattr(src_os2, attr)
                setattr(base_os2, attr, val_base | val_src)
        
        for src_font in source_fonts:
            if 'OS/2' in src_font:
                src_os2 = src_font['OS/2']
                merge_attr('ulCodePageRange1', src_os2)
                merge_attr('ulCodePageRange2', src_os2)
                merge_attr('ulUnicodeRange1', src_os2)
                merge_attr('ulUnicodeRange2', src_os2)
                merge_attr('ulUnicodeRange3', src_os2)
                merge_attr('ulUnicodeRange4', src_os2)
    
    # Prepare for in-place modification
    base_cmap = merged_font.getBestCmap()
    base_hmtx = merged_font['hmtx']
    base_glyf = merged_font['glyf']
    glyph_order = merged_font.getGlyphOrder()
    
    # We need to track which glyphs we've added to avoid duplicates
    # and to handle component renaming
    added_glyphs = {} # (source_index, source_glyph_name) -> new_glyph_name_in_merged
    
    def import_glyph(source_index, source_glyph_name):
        """
        Import a glyph from a source font into the merged font.
        Returns the name of the glyph in the merged font.
        """
        key = (source_index, source_glyph_name)
        if key in added_glyphs:
            return added_glyphs[key]
            
        source_font = source_fonts[source_index]
        source_glyf = source_glyfs[source_index]
        
        if source_glyph_name not in source_glyf:
            return '.notdef' # Fallback
            
        # Generate a new name to avoid collisions with existing base glyphs
        # unless we are explicitly replacing a base glyph, but this function 
        # is for *dependencies* (components) or *new* glyphs.
        
        # Simple renaming strategy: src{index}_{original_name}
        new_name = f"src{source_index}_{source_glyph_name}"
        
        # Check if this name already exists (unlikely with prefix, but possible)
        n = 0
        while new_name in base_glyf:
             n += 1
             new_name = f"src{source_index}_{source_glyph_name}_{n}"
             
        # Copy the glyph object
        import copy
        glyph = copy.deepcopy(source_glyf[source_glyph_name])
        
        # Handle components if composite
        if glyph.isComposite():
            for comp in glyph.components:
                comp.glyphName = import_glyph(source_index, comp.glyphName)
                
        # Add to merged font
        base_glyf[new_name] = glyph
        base_hmtx[new_name] = source_hmtxs[source_index][source_glyph_name]
        glyph_order.append(new_name)
        
        added_glyphs[key] = new_name
        return new_name

    def copy_glyph_data(source_index, source_glyph_name, target_glyph_name):
        """
        Copy glyph data from source to target name in merged font.
        Handles component recursion (importing dependencies as new glyphs).
        """
        source_glyf = source_glyfs[source_index]
        if source_glyph_name not in source_glyf:
            return # Should not happen
            
        import copy
        glyph = copy.deepcopy(source_glyf[source_glyph_name])
        
        if glyph.isComposite():
            for comp in glyph.components:
                # Dependencies are always imported as NEW glyphs to avoid 
                # messing up other existing glyphs in base font.
                comp.glyphName = import_glyph(source_index, comp.glyphName)
        
        base_glyf[target_glyph_name] = glyph
        
        # Update metrics
        orig_width, orig_lsb = source_hmtxs[source_index][source_glyph_name]
        # We will override width later in the main loop, but set LSB here
        base_hmtx[target_glyph_name] = (orig_width, orig_lsb)

    print("Processing glyphs based on pick CSV...")
    pick_counts = [0] * len(source_fonts)  # Track how many glyphs from each source
    
    for codepoint, pick_row in pick_data.items():
        pick_index_str = pick_row.get('pick', '0')
        try:
            pick_index = int(pick_index_str)
        except (ValueError, TypeError):
            pick_index = 0
        
        is_full_width = pick_row.get('is_full_width', 'False') == 'True'
        
        # Determine target advance width
        target_width = full_advance_width if is_full_width else half_advance_width
        
        if 0 <= pick_index < len(source_fonts):
            pick_counts[pick_index] += 1
            
            if pick_index == 0: # Base font
                if codepoint in base_cmap:
                    gname = base_cmap[codepoint]
                    # Update width only
                    lsb = base_hmtx[gname][1]
                    base_hmtx[gname] = (target_width, lsb)
            else: # Other font
                source_cmap = source_cmaps[pick_index]
                if codepoint in source_cmap:
                    source_gname = source_cmap[codepoint]
                    
                    if codepoint in base_cmap:
                        # Replace existing glyph
                        target_gname = base_cmap[codepoint]
                        copy_glyph_data(pick_index, source_gname, target_gname)
                        # Update width
                        lsb = base_hmtx[target_gname][1]
                        base_hmtx[target_gname] = (target_width, lsb)
                    else:
                        # New glyph
                        new_name = import_glyph(pick_index, source_gname)
                        base_cmap[codepoint] = new_name
                        # Update width
                        lsb = base_hmtx[new_name][1]
                        base_hmtx[new_name] = (target_width, lsb)
    
    # Print statistics
    print(f"Merged glyphs from {len(source_fonts)} source font(s):")
    for i, count in enumerate(pick_counts):
        print(f"  Source {i}: {count} glyphs")
    
    # Update cmap table with modified base_cmap
    print("Updating cmap table...")
    cmap_table = merged_font['cmap']
    # Find the Unicode cmap subtable (platformID=3, platEncID=1 or 10)
    target_subtable = None
    for subtable in cmap_table.tables:
        if subtable.platformID == 3 and subtable.platEncID in (1, 10):
            target_subtable = subtable
            break
    
    if target_subtable:
        target_subtable.cmap = base_cmap
    else:
        print("Warning: Could not find Unicode cmap subtable to update. Creating new one.")
        from fontTools.ttLib.tables._c_m_a_p import CmapSubtable
        new_subtable = CmapSubtable.newSubtable(4)
        new_subtable.platformID = 3
        new_subtable.platEncID = 1
        new_subtable.language = 0
        new_subtable.cmap = base_cmap
        cmap_table.tables.append(new_subtable)

    # Set glyph order
    merged_font.setGlyphOrder(glyph_order)
    
    # Update maxp table
    if 'maxp' in merged_font:
        merged_font['maxp'].numGlyphs = len(glyph_order)
    
    # Update Name Table with minimal metadata
    print(f"Setting font name to: {font_name}")
    name_table = merged_font['name']
    family_name = font_name
    subfamily_name = 'Regular'
    full_name = f"{font_name} {subfamily_name}".strip()
    unique_name = f"{font_name}-MonoMerge"
    ps_name = ''.join(ch for ch in font_name if ch.isalnum()) or 'MonoMerged'
    metadata_text = 'created by MonoMerge'
    
    # Version is timestamp
    version_string = datetime.now().strftime('%Y%m%d%H%M%S')
    
    def set_name_all_platforms(name_id, value):
        if value is None:
            return
        name_table.setName(value, name_id, 3, 1, 0x409)  # Windows Unicode
        name_table.setName(value, name_id, 1, 0, 0)      # Mac Roman
        name_table.setName(value, name_id, 0, 3, 0)      # Unicode
    
    # Set essential name records
    set_name_all_platforms(0, metadata_text)      # Copyright
    set_name_all_platforms(1, family_name)        # Font Family
    set_name_all_platforms(2, subfamily_name)     # Subfamily
    set_name_all_platforms(3, unique_name)        # Unique ID
    set_name_all_platforms(4, full_name)          # Full name
    set_name_all_platforms(5, version_string)     # Version
    set_name_all_platforms(6, ps_name)            # PostScript name
    set_name_all_platforms(8, metadata_text)      # Manufacturer
    set_name_all_platforms(9, metadata_text)      # Designer
    set_name_all_platforms(11, metadata_text)     # Vendor URL
    set_name_all_platforms(13, metadata_text)     # License
    
    # Recalculate global metrics
    print("Recalculating global metrics (head, hhea)...")
    
    head_x_min = 32767
    head_y_min = 32767
    head_x_max = -32768
    head_y_max = -32768
    
    hhea_min_lsb = 32767
    hhea_min_rsb = 32767
    hhea_max_extent = -32768
    hhea_max_advance = 0
    
    for name, (advance, lsb) in base_hmtx.metrics.items():
        hhea_max_advance = max(hhea_max_advance, advance)
        hhea_min_lsb = min(hhea_min_lsb, lsb)
        
        if name in base_glyf:
            glyph = base_glyf[name]
            # Ensure glyph has bounds calculated
            if not hasattr(glyph, 'xMin'):
                glyph.recalcBounds(base_glyf)
            
            if hasattr(glyph, 'xMin'):
                head_x_min = min(head_x_min, glyph.xMin)
                head_y_min = min(head_y_min, glyph.yMin)
                head_x_max = max(head_x_max, glyph.xMax)
                head_y_max = max(head_y_max, glyph.yMax)
                
                rsb = advance - glyph.xMax
                hhea_min_rsb = min(hhea_min_rsb, rsb)
                hhea_max_extent = max(hhea_max_extent, glyph.xMax)
    
    # Update head table
    if 'head' in merged_font:
        head = merged_font['head']
        head.xMin = head_x_min
        head.yMin = head_y_min
        head.xMax = head_x_max
        head.yMax = head_y_max
        print(f"head bbox: ({head_x_min}, {head_y_min}) - ({head_x_max}, {head_y_max})")

    # Update hhea table
    if 'hhea' in merged_font:
        hhea = merged_font['hhea']
        hhea.ascent = ascender
        hhea.descent = descender
        hhea.advanceWidthMax = hhea_max_advance
        hhea.minLeftSideBearing = hhea_min_lsb
        hhea.minRightSideBearing = hhea_min_rsb
        hhea.xMaxExtent = hhea_max_extent
        hhea.numberOfHMetrics = len(glyph_order) # Ensure this matches numGlyphs
        print(f"hhea metrics: advanceWidthMax={hhea_max_advance}, minLSB={hhea_min_lsb}, minRSB={hhea_min_rsb}, xMaxExtent={hhea_max_extent}")

    # Update OS/2 table
    if 'OS/2' in merged_font:
        merged_font['OS/2'].sTypoAscender = ascender
        merged_font['OS/2'].sTypoDescender = descender
        merged_font['OS/2'].usWinAscent = ascender
        merged_font['OS/2'].usWinDescent = abs(descender)
        
        # Set vendor ID
        merged_font['OS/2'].achVendID = vendor_id[:4].ljust(4)  # Must be exactly 4 chars
    
    # Mark font as monospace/fixed-pitch
    print("Marking font as monospace...")
    if 'post' in merged_font:
        merged_font['post'].isFixedPitch = 1
    
    if 'OS/2' in merged_font:
        # Set PANOSE bProportion to 9 (monospace)
        merged_font['OS/2'].panose.bProportion = 9
        # Set xAvgCharWidth to the half-width
        merged_font['OS/2'].xAvgCharWidth = half_advance_width
    
    # Add gasp table for better Windows rendering
    print("Adding gasp table...")
    gasp = table__g_a_s_p()
    gasp.version = 1
    gasp.gaspRange = {
        0xFFFF: GASP_SYMMETRIC_GRIDFIT | GASP_SYMMETRIC_SMOOTHING | GASP_DOGRAY | GASP_GRIDFIT
    }
    merged_font['gasp'] = gasp
    
    # Save the merged font
    print(f"Saving merged font to: {output_ttf}")
    merged_font.save(output_ttf, reorderTables=True)
    print("Done!")


def main():
    """Main entry point."""
    # Generate default font name and output path with timestamp
    today = datetime.now().strftime('%Y%m%d%H%M%S')
    default_font_name = f"test{today}"
    default_output = f"output/test{today}.ttf"
    
    parser = argparse.ArgumentParser(
        description='Merge multiple TTF fonts based on pick CSV and metadata YAML',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s input/Inconsolata-Regular.ttf input/Inconsolata-Regular.ttf,output/cjk.ttf output/pick.char.csv output/pick.meta.yaml
  %(prog)s input/Inconsolata-Regular.ttf input/Inconsolata-Regular.ttf,output/cjk.ttf output/pick.char.csv output/pick.meta.yaml -n MyFont -o output/myfont.ttf --vendor-id MYFN
        """
    )
    
    parser.add_argument(
        'input_base_ttf',
        help='Base TTF font file (e.g., input/Inconsolata-Regular.ttf)'
    )
    
    parser.add_argument(
        'input_ttf_list',
        help='Comma-separated list of TTF font files to merge (e.g., input/Inconsolata-Regular.ttf,output/cjk.ttf)'
    )
    
    parser.add_argument(
        'input_pick_csv',
        help='Pick CSV file from pick_font.py (e.g., output/pick.char.csv)'
    )
    
    parser.add_argument(
        'input_meta_yaml',
        help='Metadata YAML file from cal_meta.py (e.g., output/pick.meta.yaml)'
    )
    
    parser.add_argument(
        '--vendor-id',
        type=str,
        default='MOME',
        help='OS/2 vendor ID (4 characters, default: MOME)'
    )
    
    parser.add_argument(
        '-n', '--name',
        type=str,
        help=f'Font name (default: {default_font_name})'
    )
    
    parser.add_argument(
        '-o', '--output',
        type=str,
        help=f'Output TTF file path (default: {default_output})'
    )
    
    args = parser.parse_args()
    
    # Parse TTF list
    ttf_list = [path.strip() for path in args.input_ttf_list.split(',')]
    
    # Determine font name
    font_name = args.name if args.name else default_font_name
    
    # Determine output path
    output_ttf = args.output if args.output else default_output
    
    # Validate input files
    if not Path(args.input_base_ttf).exists():
        print(f"Error: Base font not found: {args.input_base_ttf}", file=sys.stderr)
        return 1
    
    for font_path in ttf_list:
        if not Path(font_path).exists():
            print(f"Error: Input font not found: {font_path}", file=sys.stderr)
            return 1
    
    for path in [args.input_pick_csv, args.input_meta_yaml]:
        if not Path(path).exists():
            print(f"Error: Input file not found: {path}", file=sys.stderr)
            return 1
    
    # Create output directory if needed
    Path(output_ttf).parent.mkdir(parents=True, exist_ok=True)
    
    # Perform merge
    try:
        merge_fonts(
            args.input_base_ttf,
            ttf_list,
            args.input_pick_csv,
            args.input_meta_yaml,
            output_ttf,
            font_name,
            args.vendor_id
        )
        return 0
    except Exception as e:
        print(f"Error during font merge: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        return 1


if __name__ == '__main__':
    sys.exit(main())
