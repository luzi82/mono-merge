#!/usr/bin/env python3
"""
Merge multiple TTF fonts based on character selection CSV.
Creates a new monospace font by combining glyphs from multiple source fonts.
"""

import argparse
import csv
import sys
import yaml
from datetime import datetime
from pathlib import Path
from fontTools.ttLib import TTFont
from fontTools.ttLib.tables._g_a_s_p import table__g_a_s_p, GASP_SYMMETRIC_GRIDFIT, GASP_SYMMETRIC_SMOOTHING, GASP_DOGRAY, GASP_GRIDFIT


def load_fonts(ttf_paths):
    """Load multiple TTF fonts from paths."""
    fonts = []
    for path in ttf_paths:
        print(f"Loading font: {path}")
        fonts.append(TTFont(path))
    return fonts


def load_pick_csv(csv_path):
    """Load character selection CSV file."""
    picks = {}
    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            codepoint_dec = int(row['codepoint_dec'])
            pick_index = int(row['pick'])
            is_full_width = row['is_full_width'] == 'True'
            glyph_name = row['glyph_name']
            picks[codepoint_dec] = {
                'pick': pick_index,
                'is_full_width': is_full_width,
                'glyph_name': glyph_name
            }
    return picks


def load_meta_yaml(yaml_path):
    """Load metadata YAML file."""
    with open(yaml_path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)


def create_merged_font(source_fonts, picks, meta, font_name, vendor_id, version_date):
    """Create a new merged font from source fonts based on character picks."""
    
    # Use the first source font as the base template
    base_font = source_fonts[0]
    
    # Create a new font using the base font as template
    print("Creating new merged font...")
    merged_font = TTFont()
    
    # Copy essential tables from base font
    for table_tag in ['head', 'hhea', 'maxp', 'OS/2', 'post', 'name', 'cmap']:
        if table_tag in base_font:
            merged_font[table_tag] = base_font[table_tag]
    
    # Create new glyf and loca tables
    from fontTools.ttLib.tables._g_l_y_f import table__g_l_y_f
    from fontTools.ttLib.tables._l_o_c_a import table__l_o_c_a
    
    glyf_table = table__g_l_y_f()
    glyf_table.glyphs = {}
    
    # Create new hmtx table for horizontal metrics
    from fontTools.ttLib.tables._h_m_t_x import table__h_m_t_x
    hmtx_table = table__h_m_t_x()
    hmtx_table.metrics = {}
    
    # Build glyph order and copy glyphs
    glyph_order = ['.notdef']  # .notdef must be first
    glyph_name_set = {'.notdef'}
    
    # Track which glyph names came from which source font to prevent overwrites
    glyph_name_to_source = {}  # Maps final glyph name to (source_index, original_name)
    
    # First, add .notdef from base font
    if '.notdef' in base_font['glyf']:
        glyf_table.glyphs['.notdef'] = base_font['glyf']['.notdef']
        hmtx_table.metrics['.notdef'] = base_font['hmtx']['.notdef']
        glyph_name_to_source['.notdef'] = (0, '.notdef')
    
    # Track components that need to be added
    components_to_add = set()
    
    # Build cmap (character to glyph mapping)
    from fontTools.ttLib.tables._c_m_a_p import table__c_m_a_p
    cmap_table = table__c_m_a_p()
    cmap_subtables = []
    
    # Create Unicode BMP subtable (format 4, platform 3, encoding 1) for U+0000-U+FFFF
    from fontTools.ttLib.tables._c_m_a_p import CmapSubtable
    cmap_subtable_4 = CmapSubtable.newSubtable(4)
    cmap_subtable_4.platformID = 3
    cmap_subtable_4.platEncID = 1
    cmap_subtable_4.language = 0
    cmap_subtable_4.cmap = {}
    
    # Create Unicode full repertoire subtable (format 12, platform 3, encoding 10) for all Unicode
    cmap_subtable_12 = CmapSubtable.newSubtable(12)
    cmap_subtable_12.platformID = 3
    cmap_subtable_12.platEncID = 10
    cmap_subtable_12.language = 0
    cmap_subtable_12.cmap = {}
    
    # Process each character according to pick CSV
    print(f"Processing {len(picks)} characters...")
    for codepoint, pick_info in sorted(picks.items()):
        pick_index = pick_info['pick']
        is_full_width = pick_info['is_full_width']
        glyph_name = pick_info['glyph_name']
        
        # Ensure glyph_name is a string
        if not isinstance(glyph_name, str):
            print(f"Warning: glyph_name for U+{codepoint:04X} is {type(glyph_name)}: {repr(glyph_name)}, converting to string")
            glyph_name = str(glyph_name)
        
        # Select the source font
        if pick_index >= len(source_fonts):
            print(f"Warning: Pick index {pick_index} out of range for codepoint U+{codepoint:04X}, using first font")
            pick_index = 0
        
        source_font = source_fonts[pick_index]
        
        # Copy glyph from source font
        if glyph_name in source_font['glyf']:
            # Check if this glyph name is already used by a different source font
            final_glyph_name = glyph_name
            if glyph_name in glyph_name_to_source:
                existing_source, _ = glyph_name_to_source[glyph_name]
                if existing_source != pick_index:
                    # Name conflict - create a unique name
                    final_glyph_name = f"{glyph_name}_src{pick_index}"
                    counter = 1
                    while final_glyph_name in glyph_name_set:
                        final_glyph_name = f"{glyph_name}_src{pick_index}_{counter}"
                        counter += 1
                    print(f"  Renaming glyph '{glyph_name}' from source {pick_index} to '{final_glyph_name}' to avoid conflict")
            
            # Copy glyph with the final name
            glyf_table.glyphs[final_glyph_name] = source_font['glyf'][glyph_name]
            
            # Set advance width based on full/half width
            if is_full_width:
                advance_width = meta['full_advance_width']
            else:
                advance_width = meta['half_advance_width']
            
            # Get original lsb or use 0
            try:
                if glyph_name in source_font['hmtx'].metrics:
                    _, original_lsb = source_font['hmtx'].metrics[glyph_name]
                else:
                    original_lsb = 0
            except (KeyError, AttributeError):
                original_lsb = 0
            
            hmtx_table.metrics[final_glyph_name] = (advance_width, original_lsb)
            
            # Add to glyph order if not already present
            if final_glyph_name not in glyph_name_set:
                glyph_order.append(final_glyph_name)
                glyph_name_set.add(final_glyph_name)
                glyph_name_to_source[final_glyph_name] = (pick_index, glyph_name)
            
            # Map character to glyph (using final glyph name)
            if codepoint <= 0xFFFF:
                # BMP characters go in both format 4 and format 12
                cmap_subtable_4.cmap[codepoint] = final_glyph_name
            # All characters go in format 12
            cmap_subtable_12.cmap[codepoint] = final_glyph_name
            
            # Check for composite glyph components
            glyph = glyf_table.glyphs[final_glyph_name]
            if glyph.isComposite():
                for component in glyph.components:
                    comp_name = component.glyphName
                    if comp_name not in glyph_name_set:
                        components_to_add.add((comp_name, pick_index))
    
    # Add component glyphs recursively
    while components_to_add:
        comp_name, source_index = components_to_add.pop()
        
        # Check if we already have this component from the same source
        if comp_name in glyph_name_to_source:
            existing_source, _ = glyph_name_to_source[comp_name]
            if existing_source == source_index:
                # Already have this glyph from the same source
                continue
        
        # Ensure comp_name is a string
        if not isinstance(comp_name, str):
            comp_name = str(comp_name)
        
        source_font = source_fonts[source_index]
        
        if comp_name in source_font['glyf']:
            # Check for name conflict
            final_comp_name = comp_name
            if comp_name in glyph_name_to_source:
                existing_source, _ = glyph_name_to_source[comp_name]
                if existing_source != source_index:
                    # Name conflict - create a unique name
                    final_comp_name = f"{comp_name}_src{source_index}"
                    counter = 1
                    while final_comp_name in glyph_name_set:
                        final_comp_name = f"{comp_name}_src{source_index}_{counter}"
                        counter += 1
                    print(f"  Renaming component '{comp_name}' from source {source_index} to '{final_comp_name}' to avoid conflict")
            
            # Copy component glyph
            glyf_table.glyphs[final_comp_name] = source_font['glyf'][comp_name]
            
            # Copy metrics
            try:
                if comp_name in source_font['hmtx'].metrics:
                    hmtx_table.metrics[final_comp_name] = source_font['hmtx'].metrics[comp_name]
                else:
                    hmtx_table.metrics[final_comp_name] = (0, 0)
            except (KeyError, AttributeError):
                hmtx_table.metrics[final_comp_name] = (0, 0)
            
            # Add to glyph order if not already present
            if final_comp_name not in glyph_name_set:
                glyph_order.append(final_comp_name)
                glyph_name_set.add(final_comp_name)
                glyph_name_to_source[final_comp_name] = (source_index, comp_name)
            
            # Check if this component has sub-components
            glyph = glyf_table.glyphs[final_comp_name]
            if glyph.isComposite():
                for component in glyph.components:
                    sub_comp_name = component.glyphName
                    if sub_comp_name not in glyph_name_set:
                        components_to_add.add((sub_comp_name, source_index))
    
    print(f"Total glyphs in merged font: {len(glyph_order)}")
    
    # Set glyph table
    glyf_table.glyphOrder = glyph_order
    merged_font['glyf'] = glyf_table
    merged_font.setGlyphOrder(glyph_order)
    
    # Set loca table
    loca_table = table__l_o_c_a()
    merged_font['loca'] = loca_table
    
    # Set hmtx table
    merged_font['hmtx'] = hmtx_table
    
    # Set cmap table
    cmap_table.tableVersion = 0
    cmap_table.tables = [cmap_subtable_4, cmap_subtable_12]
    merged_font['cmap'] = cmap_table
    
    # Update name table
    print(f"Setting font name to: {font_name}")
    name_table = merged_font['name']
    family_name = font_name
    subfamily_name = 'Regular'
    full_name = f"{font_name} {subfamily_name}".strip()
    unique_name = f"{font_name}-MonoMerge"
    ps_name = ''.join(ch for ch in font_name if ch.isalnum()) or 'MonoMerged'
    metadata_text = 'created by MonoMerge'
    version_string = version_date

    def set_name_all_platforms(name_id, value):
        if value is None:
            return
        name_table.setName(value, name_id, 3, 1, 0x409)
        name_table.setName(value, name_id, 1, 0, 0)
        name_table.setName(value, name_id, 0, 3, 0)

    # Clear and set name records
    name_table.names = []
    set_name_all_platforms(0, metadata_text)  # Copyright
    set_name_all_platforms(1, family_name)  # Font Family
    set_name_all_platforms(2, subfamily_name)  # Subfamily
    set_name_all_platforms(3, unique_name)  # Unique ID
    set_name_all_platforms(4, full_name)  # Full name
    set_name_all_platforms(5, version_string)  # Version
    set_name_all_platforms(6, ps_name)  # PostScript name
    set_name_all_platforms(8, metadata_text)  # Manufacturer
    set_name_all_platforms(9, metadata_text)  # Designer
    set_name_all_platforms(11, metadata_text)  # Vendor URL
    set_name_all_platforms(13, metadata_text)  # License
    
    # Update OS/2 table
    print("Configuring OS/2 table for monospace...")
    if 'OS/2' in merged_font:
        os2 = merged_font['OS/2']
        
        # Set vendor ID
        os2.achVendID = vendor_id
        
        # Set ascender and descender
        os2.sTypoAscender = meta['ascender']
        os2.sTypoDescender = meta['descender']
        os2.usWinAscent = meta['ascender']
        os2.usWinDescent = abs(meta['descender'])
        
        # Mark as monospace
        os2.panose.bProportion = 9  # Monospace
        os2.xAvgCharWidth = meta['half_advance_width']
        
        # Recalculate Unicode ranges based on actual characters in cmap
        print("Recalculating Unicode ranges...")
        os2.recalcUnicodeRanges(merged_font)
        
        # Manually ensure CJK bit is set if we have CJK characters
        # Bit 59 = CJK Unified Ideographs (U+4E00-U+9FFF)
        # This is in ulUnicodeRange2 (bits 32-63), so bit (59-32) = bit 27
        cmap = merged_font.getBestCmap()
        if cmap:
            has_cjk = any(0x4E00 <= cp <= 0x9FFF for cp in cmap.keys())
            if has_cjk:
                print("CJK characters detected, setting Unicode and CodePage ranges...")
                os2.ulUnicodeRange2 |= (1 << 27)  # Set bit 59 (CJK Unified Ideographs)
                # Set CodePage bits for Chinese support (helps Windows recognize the font)
                os2.ulCodePageRange1 |= (1 << 17)  # Bit 17: Chinese: Traditional (Big5)
                os2.ulCodePageRange1 |= (1 << 18)  # Bit 18: Chinese: Simplified (PRC and Singapore)
                os2.ulCodePageRange1 |= (1 << 20)  # Bit 20: Chinese: Traditional (Taiwan)
    
    # Update hhea table
    if 'hhea' in merged_font:
        merged_font['hhea'].ascent = meta['ascender']
        merged_font['hhea'].descent = meta['descender']
    
    # Update post table - mark as fixed pitch
    print("Marking font as monospace/fixed-pitch...")
    if 'post' in merged_font:
        post_table = merged_font['post']
        post_table.isFixedPitch = 1
        post_table.formatType = 3.0  # No glyph names
        post_table.extraNames = []
        post_table.mapping = {}
    
    # Add gasp table for better rendering
    print("Adding gasp table for improved rendering...")
    gasp = table__g_a_s_p()
    gasp.version = 1
    gasp.gaspRange = {
        0xFFFF: GASP_SYMMETRIC_GRIDFIT | GASP_SYMMETRIC_SMOOTHING | GASP_DOGRAY | GASP_GRIDFIT
    }
    merged_font['gasp'] = gasp
    
    # Remove unnecessary tables
    tables_to_remove = ['DSIG', 'meta', 'GPOS', 'GSUB']
    for table_tag in tables_to_remove:
        if table_tag in merged_font:
            del merged_font[table_tag]
    
    return merged_font


def main():
    parser = argparse.ArgumentParser(
        description='Merge multiple TTF fonts based on character selection',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Example:
  %(prog)s input/Inconsolata-Regular.ttf,output/cjk.ttf output/pick.char.csv output/pick.meta.yaml --output output/merged.ttf
        """
    )
    
    parser.add_argument(
        'input_ttf_list',
        type=str,
        help='Comma-separated list of input TTF files (e.g., input/font1.ttf,input/font2.ttf)'
    )
    
    parser.add_argument(
        'input_pick_csv',
        type=str,
        help='CSV file with character-to-font mappings (created by ttf/pick_font.py)'
    )
    
    parser.add_argument(
        'input_meta_yaml',
        type=str,
        help='YAML file with font metadata (created by ttf/cal_meta.py)'
    )
    
    parser.add_argument(
        '--vendor-id',
        type=str,
        default='MOME',
        help='OS/2 vendor ID (default: MOME)'
    )
    
    parser.add_argument(
        '--font-name',
        type=str,
        help='Font name (default: test{yyyymmddhhmmss})'
    )
    
    parser.add_argument(
        '--output',
        type=str,
        help='Output TTF file (default: output/test{yyyymmddhhmmss}.ttf)'
    )
    
    args = parser.parse_args()
    
    # Validate vendor ID format
    if len(args.vendor_id) != 4:
        print(f"Error: Vendor ID must be exactly 4 characters, got: '{args.vendor_id}' ({len(args.vendor_id)} chars)", file=sys.stderr)
        sys.exit(1)
    
    if not args.vendor_id.isascii():
        print(f"Error: Vendor ID must contain only ASCII characters, got: '{args.vendor_id}'", file=sys.stderr)
        sys.exit(1)
    
    # Parse input font list
    ttf_paths = [p.strip() for p in args.input_ttf_list.split(',')]
    
    # Validate input files
    for path in ttf_paths:
        if not Path(path).exists():
            print(f"Error: Font file not found: {path}", file=sys.stderr)
            sys.exit(1)
    
    if not Path(args.input_pick_csv).exists():
        print(f"Error: Pick CSV file not found: {args.input_pick_csv}", file=sys.stderr)
        sys.exit(1)
    
    if not Path(args.input_meta_yaml).exists():
        print(f"Error: Meta YAML file not found: {args.input_meta_yaml}", file=sys.stderr)
        sys.exit(1)
    
    # Generate default font name and output path if needed
    timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
    font_name = args.font_name if args.font_name else f"test{timestamp}"
    output_path = args.output if args.output else f"output/test{timestamp}.ttf"
    
    # Replace DATETIME placeholder in output path and font name
    if "DATETIME" in output_path:
        output_path = output_path.replace("DATETIME", timestamp)
    
    if "DATETIME" in font_name:
        font_name = font_name.replace("DATETIME", timestamp)
    
    # Ensure output directory exists
    output_dir = Path(output_path).parent
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Load fonts
    source_fonts = load_fonts(ttf_paths)
    
    # Load pick CSV
    print(f"Loading pick CSV: {args.input_pick_csv}")
    picks = load_pick_csv(args.input_pick_csv)
    
    # Load metadata
    print(f"Loading metadata: {args.input_meta_yaml}")
    meta = load_meta_yaml(args.input_meta_yaml)
    
    print(f"Metadata: half_width={meta['half_advance_width']}, full_width={meta['full_advance_width']}")
    print(f"Metadata: ascender={meta['ascender']}, descender={meta['descender']}")
    
    # Create merged font
    merged_font = create_merged_font(
        source_fonts,
        picks,
        meta,
        font_name,
        args.vendor_id,
        timestamp
    )
    
    # Save merged font
    print(f"Saving merged font to: {output_path}")
    merged_font.save(output_path, reorderTables=True)
    print("Done!")


if __name__ == '__main__':
    main()
