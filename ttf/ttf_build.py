import argparse
import csv
import sys
import datetime
from fontTools.ttLib import TTFont
from fontTools.ttLib.tables._g_l_y_f import Glyph
from fontTools.ttLib.tables._g_a_s_p import table__g_a_s_p
from fontTools.ttLib.tables._c_m_a_p import CmapSubtable

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('input_codepoint_csv')
    parser.add_argument('input_ttf_list')
    parser.add_argument('--default', required=True)
    parser.add_argument('--font-name')
    parser.add_argument('--url-vendor')
    parser.add_argument('--vendor-id')
    parser.add_argument('--name-unique-id')
    parser.add_argument('--license')
    parser.add_argument('--copyright')
    parser.add_argument('--manufacturer')
    parser.add_argument('--designer')
    parser.add_argument('--version')
    parser.add_argument('--ascender', type=int)
    parser.add_argument('--descender', type=int)
    parser.add_argument('--xAvgCharWidth', type=int)
    parser.add_argument('--unitsPerEm', type=int)
    parser.add_argument('output_ttf')
    
    args = parser.parse_args()
    
    # Parse input_ttf_list
    ttf_map = {}
    for item in args.input_ttf_list.split(','):
        if ':' not in item:
            continue
        name, path = item.split(':', 1)
        ttf_map[name] = TTFont(path)
        
    base_font_name = args.default
    if base_font_name not in ttf_map:
        raise ValueError(f"Default font '{base_font_name}' not found in input_ttf_list")
        
    base_font = ttf_map[base_font_name]
    
    # Read CSV
    glyph_data = []
    with open(args.input_codepoint_csv, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            glyph_data.append(row)
            
    # Sort by glyph_index
    glyph_data.sort(key=lambda x: int(x['glyph_index']))
    
    # Prepare new tables
    new_glyph_order = ['.notdef']
    new_glyphs = {}
    new_hmtx = {}
    new_cmap = {}
    
    # Get .notdef from base font
    base_glyf = base_font['glyf']
    base_hmtx = base_font['hmtx']
    
    if '.notdef' in base_glyf:
        new_glyphs['.notdef'] = base_glyf['.notdef']
        new_hmtx['.notdef'] = base_hmtx['.notdef']
    else:
        # Create empty .notdef if missing (unlikely)
        new_glyphs['.notdef'] = Glyph()
        new_hmtx['.notdef'] = (args.xAvgCharWidth or 500, 0)

    # Process CSV rows
    for row in glyph_data:
        g_idx = int(row['glyph_index'])
        src_name = row['src']
        src_g_idx = int(row['src_glyph_index'])
        codepoint_str = row['codepoint']
        glyph_name = row['glyph_name']
        
        # Parse codepoint
        if codepoint_str.startswith('U+'):
            codepoint = int(codepoint_str[2:], 16)
        else:
            try:
                codepoint = int(codepoint_str)
            except ValueError:
                continue # Skip invalid codepoints
        
        # Ensure glyph order continuity
        # If g_idx is 1, it should be at index 1 (0 is .notdef)
        
        # Handle index 0
        if g_idx == 0:
            # Overwrite .notdef
            if src_name not in ttf_map:
                raise ValueError(f"Source '{src_name}' not found in input_ttf_list")
            src_font = ttf_map[src_name]
            src_glyf_table = src_font['glyf']
            src_hmtx_table = src_font['hmtx']
            try:
                src_glyph_name = src_font.getGlyphOrder()[src_g_idx]
            except IndexError:
                 raise ValueError(f"Source glyph index {src_g_idx} out of range for {src_name}")
            glyph = src_glyf_table[src_glyph_name]
            if glyph.isComposite():
                raise Exception(f"Composite glyph found at {codepoint_str} from {src_name}")
            
            new_glyphs['.notdef'] = glyph
            new_hmtx['.notdef'] = src_hmtx_table[src_glyph_name]
            # .notdef is already in new_glyph_order[0]
            continue

        # Handle gaps
        while len(new_glyph_order) < g_idx:
            # Fill with empty glyph
            gap_name = f"empty{len(new_glyph_order)}"
            new_glyphs[gap_name] = Glyph()
            new_hmtx[gap_name] = (0, 0)
            new_glyph_order.append(gap_name)
        
        if src_name not in ttf_map:
            raise ValueError(f"Source '{src_name}' not found in input_ttf_list")
            
        src_font = ttf_map[src_name]
        src_glyf_table = src_font['glyf']
        src_hmtx_table = src_font['hmtx']
        
        # Get source glyph name
        try:
            src_glyph_name = src_font.getGlyphOrder()[src_g_idx]
        except IndexError:
             raise ValueError(f"Source glyph index {src_g_idx} out of range for {src_name}")
        
        glyph = src_glyf_table[src_glyph_name]
        
        # Check for composite
        if glyph.isComposite():
            raise Exception(f"Composite glyph found at {codepoint_str} from {src_name}")
            
        # Add to new lists
        if glyph_name not in new_glyphs:
            new_glyphs[glyph_name] = glyph
            new_hmtx[glyph_name] = src_hmtx_table[src_glyph_name]
            new_glyph_order.append(glyph_name)
        
        new_cmap[codepoint] = glyph_name

    # Update base_font
    base_font.setGlyphOrder(new_glyph_order)
    base_font['glyf'].glyphs = new_glyphs
    base_font['hmtx'].metrics = new_hmtx
    
    # Rebuild cmap
    cmap_table = base_font['cmap']
    cmap_table.tables = [] 
    
    # Format 4 (BMP)
    cmap4 = CmapSubtable.newSubtable(4)
    cmap4.platformID = 3
    cmap4.platEncID = 1
    cmap4.language = 0
    cmap4.cmap = {k:v for k,v in new_cmap.items() if k <= 0xFFFF}
    cmap_table.tables.append(cmap4)
    
    # Format 12 (Full Unicode)
    if any(k > 0xFFFF for k in new_cmap.keys()):
        cmap12 = CmapSubtable.newSubtable(12)
        cmap12.platformID = 3
        cmap12.platEncID = 10
        cmap12.language = 0
        cmap12.cmap = new_cmap
        cmap_table.tables.append(cmap12)
        
    # Update Name Table
    name_table = base_font['name']
    # Helper to set name record
    def set_name(nameID, string):
        if string:
            name_table.setName(string, nameID, 3, 1, 1033) # Windows English
            name_table.setName(string, nameID, 1, 0, 0)    # Mac English

    if args.font_name:
        set_name(1, args.font_name) # Family Name
        set_name(3, args.name_unique_id or f"{args.font_name}-{args.version}") # Unique ID
        set_name(4, args.font_name) # Full Name
        set_name(6, args.font_name.replace(" ", "")) # PostScript Name

    if args.version:
        set_name(5, f"Version {args.version}")
    
    if args.copyright:
        set_name(0, args.copyright)
    
    if args.manufacturer:
        set_name(8, args.manufacturer)
        
    if args.designer:
        set_name(9, args.designer)
        
    if args.url_vendor:
        set_name(11, args.url_vendor)
        
    if args.license:
        set_name(13, args.license)

    # Update OS/2 Table
    os2 = base_font['OS/2']
    if args.vendor_id:
        os2.achVendID = args.vendor_id
        
    if args.ascender is not None:
        os2.sTypoAscender = args.ascender
        os2.usWinAscent = args.ascender
        
    if args.descender is not None:
        os2.sTypoDescender = args.descender
        os2.usWinDescent = abs(args.descender)
        
    if args.xAvgCharWidth is not None:
        os2.xAvgCharWidth = args.xAvgCharWidth
        
    # Monospace settings
    os2.panose.bProportion = 9
    
    # Update hhea
    hhea = base_font['hhea']
    if args.ascender is not None:
        hhea.ascent = args.ascender
    if args.descender is not None:
        hhea.descent = args.descender
        
    # Update head
    head = base_font['head']
    if args.unitsPerEm is not None:
        head.unitsPerEm = args.unitsPerEm
        
    # Post table
    post = base_font['post']
    post.formatType = 3.0
    post.isFixedPitch = 1
    post.extraNames = []
    post.mapping = {}
    
    # Recalculate Unicode ranges
    print("Recalculating Unicode ranges...")
    os2.recalcUnicodeRanges(base_font)
    
    # CJK Detection (from merge_font.py)
    has_cjk = any(0x4E00 <= cp <= 0x9FFF for cp in new_cmap.keys())
    if has_cjk:
        print("CJK characters detected, setting Unicode and CodePage ranges...")
        os2.ulUnicodeRange2 |= (1 << 27)  # Set bit 59 (CJK Unified Ideographs)
        # Set CodePage bits for Chinese support
        os2.ulCodePageRange1 |= (1 << 17)  # Bit 17: Chinese: Traditional (Big5)
        os2.ulCodePageRange1 |= (1 << 18)  # Bit 18: Chinese: Simplified (PRC and Singapore)
        os2.ulCodePageRange1 |= (1 << 20)  # Bit 20: Chinese: Traditional (Taiwan)

    # Save
    print(f"Saving to {args.output_ttf}")
    base_font.save(args.output_ttf)

if __name__ == '__main__':
    main()
