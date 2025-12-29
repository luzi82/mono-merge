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
    
    # Create output font based on base font
    print("Creating merged font...")
    merged_font = TTFont()
    
    # Copy essential tables from base font (but NOT glyf, hmtx, cmap - we'll rebuild those)
    for table_tag in ['head', 'hhea', 'maxp', 'OS/2', 'name', 'post']:
        if table_tag in base_font:
            merged_font[table_tag] = base_font[table_tag]

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
    
    # Get cmap, hmtx, and glyf for base font and all source fonts
    base_cmap = base_font.getBestCmap()
    base_hmtx = base_font['hmtx']
    base_glyf = base_font['glyf']
    
    source_cmaps = [font.getBestCmap() for font in source_fonts]
    source_hmtxs = [font['hmtx'] for font in source_fonts]
    source_glyfs = [font['glyf'] for font in source_fonts]
    
    # Build merged glyph data
    merged_glyphs = {}
    merged_metrics = {}
    glyph_order = []
    codepoint_to_glyph = {}
    
    # Always keep .notdef from base font
    if '.notdef' in base_glyf:
        merged_glyphs['.notdef'] = base_glyf['.notdef']
        if '.notdef' in base_hmtx.metrics:
            merged_metrics['.notdef'] = base_hmtx.metrics['.notdef']
        else:
            merged_metrics['.notdef'] = (half_advance_width, 0)
        glyph_order.append('.notdef')
    
    def copy_glyph_recursive(glyph_name, source_glyf, source_hmtx, target_width):
        """Recursively copy a glyph and all its component dependencies."""
        if glyph_name in merged_glyphs or glyph_name not in source_glyf:
            return
        
        # Copy the glyph
        merged_glyphs[glyph_name] = source_glyf[glyph_name]
        glyph_order.append(glyph_name)
        
        # Copy metrics
        if glyph_name in source_hmtx.metrics:
            orig_width, orig_lsb = source_hmtx.metrics[glyph_name]
            merged_metrics[glyph_name] = (orig_width, orig_lsb)
        else:
            merged_metrics[glyph_name] = (target_width, 0)
        
        # Recursively copy component glyphs
        glyph = source_glyf[glyph_name]
        if glyph.isComposite():
            for component in glyph.components:
                comp_glyph_name = component.glyphName
                copy_glyph_recursive(comp_glyph_name, source_glyf, source_hmtx, target_width)
    
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
        
        # Get glyph name for this codepoint from the selected source
        glyph_name = None
        source_glyf = None
        source_hmtx = None
        
        if 0 <= pick_index < len(source_fonts):
            source_cmap = source_cmaps[pick_index]
            if codepoint in source_cmap:
                glyph_name = source_cmap[codepoint]
                source_glyf = source_glyfs[pick_index]
                source_hmtx = source_hmtxs[pick_index]
                pick_counts[pick_index] += 1
        
        if glyph_name and glyph_name in source_glyf:
            # Skip if already copied
            if glyph_name in merged_glyphs:
                # Update metrics for this specific codepoint
                if glyph_name in source_hmtx.metrics:
                    lsb = source_hmtx.metrics[glyph_name][1]
                else:
                    lsb = 0
                merged_metrics[glyph_name] = (target_width, lsb)
                codepoint_to_glyph[codepoint] = glyph_name
                continue
            
            # Recursively copy glyph and all components
            copy_glyph_recursive(glyph_name, source_glyf, source_hmtx, target_width)
            
            # Set advance width for this main glyph
            if glyph_name in source_hmtx.metrics:
                lsb = source_hmtx.metrics[glyph_name][1]
            else:
                lsb = 0
            merged_metrics[glyph_name] = (target_width, lsb)
            
            # Track codepoint to glyph mapping for cmap
            codepoint_to_glyph[codepoint] = glyph_name
    
    # Print statistics
    print(f"Merged glyphs from {len(source_fonts)} source font(s):")
    for i, count in enumerate(pick_counts):
        print(f"  Source {i}: {count} glyphs")
    
    # Create and populate glyf table
    from fontTools.ttLib.tables._g_l_y_f import table__g_l_y_f
    glyf_table = table__g_l_y_f()
    glyf_table.glyphs = merged_glyphs
    glyf_table.glyphOrder = glyph_order
    merged_font['glyf'] = glyf_table
    
    # Create and populate loca table
    from fontTools.ttLib.tables._l_o_c_a import table__l_o_c_a
    loca_table = table__l_o_c_a()
    merged_font['loca'] = loca_table
    
    # Create and populate hmtx table
    from fontTools.ttLib.tables._h_m_t_x import table__h_m_t_x
    hmtx_table = table__h_m_t_x()
    hmtx_table.metrics = merged_metrics
    merged_font['hmtx'] = hmtx_table
    
    # Create and populate cmap table
    from fontTools.ttLib.tables._c_m_a_p import table__c_m_a_p, CmapSubtable
    cmap_table = table__c_m_a_p()
    cmap_table.tableVersion = 0
    
    # Create format 4 subtable for BMP (codepoints <= 0xFFFF)
    cmap_subtable_4 = CmapSubtable.newSubtable(4)
    cmap_subtable_4.platformID = 3
    cmap_subtable_4.platEncID = 1
    cmap_subtable_4.language = 0
    cmap_subtable_4.cmap = {cp: gn for cp, gn in codepoint_to_glyph.items() if cp <= 0xFFFF}
    
    # Create format 12 subtable for full Unicode (supports all codepoints)
    cmap_subtable_12 = CmapSubtable.newSubtable(12)
    cmap_subtable_12.platformID = 3
    cmap_subtable_12.platEncID = 10
    cmap_subtable_12.language = 0
    cmap_subtable_12.cmap = codepoint_to_glyph
    
    cmap_table.tables = [cmap_subtable_4, cmap_subtable_12]
    merged_font['cmap'] = cmap_table
    
    # Set glyph order
    merged_font.setGlyphOrder(glyph_order)
    
    # Remove unnecessary metadata tables
    print("Cleaning unnecessary metadata tables...")
    for table_tag in ['DSIG', 'meta']:
        if table_tag in merged_font:
            del merged_font[table_tag]
    
    # Simplify post table (format 3.0 = no glyph names stored)
    if 'post' in merged_font:
        post_table = merged_font['post']
        post_table.formatType = 3.0
        post_table.extraNames = []
        post_table.mapping = {}
    
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
    
    # Remove all existing name records
    name_table.names = []
    
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
    
    for name, (advance, lsb) in merged_metrics.items():
        hhea_max_advance = max(hhea_max_advance, advance)
        hhea_min_lsb = min(hhea_min_lsb, lsb)
        
        if name in merged_glyphs:
            glyph = merged_glyphs[name]
            # Ensure glyph has bounds calculated
            if not hasattr(glyph, 'xMin'):
                glyph.recalcBounds(merged_glyphs)
            
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
