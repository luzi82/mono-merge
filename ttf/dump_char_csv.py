#!/usr/bin/env python3
"""
Dump TTF character information to CSV files.
Outputs codepoint mapping and glyph metrics to separate CSV files.
"""
import argparse
import csv
import sys
import math
from collections import Counter
from fontTools.ttLib import TTFont


def calculate_width_unit(advance_width, reference_width):
    """
    Calculate width_unit based on advance_width/reference_width ratio.
    - if advance_width <= 0, return 0
    - if reference_width is None or <= 0, return 0
    - if ratio <= sqrt(1*2), return 1
    - if ratio <= sqrt(2*3), return 2
    - if ratio <= sqrt(3*4), return 3
    - etc.
    """
    if advance_width is None or advance_width <= 0:
        return 0
    
    if reference_width is None or reference_width <= 0:
        return 0
    
    ratio = advance_width / reference_width
    
    n = 1
    while True:
        threshold = math.sqrt(n * (n + 1))
        if ratio <= threshold:
            return n
        n += 1


def dump_font_to_csv(input_ttf, output_codepoint_csv, output_glyph_csv, output_glyphref_csv):
    """
    Extract character information from TTF file and write to three CSV files.
    
    Args:
        input_ttf: Path to input TTF file
        output_codepoint_csv: Path to output codepoint mapping CSV file
        output_glyph_csv: Path to output glyph metrics CSV file
        output_glyphref_csv: Path to output glyph reference relationship CSV file
    """
    try:
        font = TTFont(input_ttf)
    except Exception as e:
        print(f"Error loading font: {e}", file=sys.stderr)
        sys.exit(1)
    
    # Get necessary tables
    cmap = font.getBestCmap()
    if not cmap:
        print("Error: No suitable cmap found in font", file=sys.stderr)
        sys.exit(1)
    
    glyf = font.get('glyf')
    hmtx = font.get('hmtx')
    vmtx = font.get('vmtx')
    head = font.get('head')
    
    if not glyf:
        print("Error: No glyf table found (not a TrueType font?)", file=sys.stderr)
        sys.exit(1)
    
    if not hmtx:
        print("Error: No hmtx table found", file=sys.stderr)
        sys.exit(1)
    
    # Determine reference width for full-width detection (use space character U+0020)
    reference_width = None
    if 0x0020 in cmap:  # ASCII space
        space_glyph = cmap[0x0020]
        if space_glyph in hmtx.metrics:
            reference_width, _ = hmtx.metrics[space_glyph]
    
    # If space not found, try 'A' (U+0041)
    if reference_width is None and 0x0041 in cmap:
        a_glyph = cmap[0x0041]
        if a_glyph in hmtx.metrics:
            reference_width, _ = hmtx.metrics[a_glyph]
    
    # Track which glyphs are used by codepoints
    glyphs_cmap_count = Counter()
    for codepoint in cmap.keys():
        glyph_name = cmap[codepoint]
        glyphs_cmap_count[glyph_name] += 1
    
    # Track which glyphs are used as components in composite glyphs
    glyphs_glyf_count = Counter()
    # Track composite glyph references and count references per glyph
    glyphref_rows = []
    glyph_num_refs = Counter()  # Count how many glyphs each glyph references
    for glyph_name in glyf.keys():
        glyph = glyf[glyph_name]
        if glyph.isComposite():
            for component in glyph.components:
                glyphs_glyf_count[component.glyphName] += 1
                # Record reference relationship
                glyphref_rows.append({
                    'ref_from': glyph_name,
                    'ref_to': component.glyphName
                })
                glyph_num_refs[glyph_name] += 1
    
    # Track which glyphs are used in GSUB table
    glyphs_gsub_count = Counter()
    gsub = font.get('GSUB')
    if gsub and hasattr(gsub, 'table'):
        for lookup in gsub.table.LookupList.Lookup:
            for subtable in lookup.SubTable:
                # Collect glyphs from various GSUB subtable types
                if hasattr(subtable, 'mapping'):
                    for key in subtable.mapping.keys():
                        glyphs_gsub_count[key] += 1
                    for value in subtable.mapping.values():
                        if isinstance(value, list):
                            for glyph in value:
                                glyphs_gsub_count[glyph] += 1
                        else:
                            glyphs_gsub_count[value] += 1
                if hasattr(subtable, 'ligatures'):
                    for glyph_name, ligatures in subtable.ligatures.items():
                        glyphs_gsub_count[glyph_name] += 1
                        for ligature in ligatures:
                            glyphs_gsub_count[ligature.LigGlyph] += 1
                            for comp in ligature.Component:
                                glyphs_gsub_count[comp] += 1
                if hasattr(subtable, 'alternates'):
                    for glyph_name, alts in subtable.alternates.items():
                        glyphs_gsub_count[glyph_name] += 1
                        for alt in alts:
                            glyphs_gsub_count[alt] += 1
                if hasattr(subtable, 'Coverage'):
                    if hasattr(subtable.Coverage, 'glyphs'):
                        for glyph in subtable.Coverage.glyphs:
                            glyphs_gsub_count[glyph] += 1
    
    # Track which glyphs are used in GPOS table
    glyphs_gpos_count = Counter()
    gpos = font.get('GPOS')
    if gpos and hasattr(gpos, 'table'):
        for lookup in gpos.table.LookupList.Lookup:
            for subtable in lookup.SubTable:
                # Collect glyphs from various GPOS subtable types
                if hasattr(subtable, 'Coverage'):
                    if hasattr(subtable.Coverage, 'glyphs'):
                        for glyph in subtable.Coverage.glyphs:
                            glyphs_gpos_count[glyph] += 1
                if hasattr(subtable, 'ClassDef1'):
                    if hasattr(subtable.ClassDef1, 'classDefs'):
                        for glyph in subtable.ClassDef1.classDefs.keys():
                            glyphs_gpos_count[glyph] += 1
                if hasattr(subtable, 'ClassDef2'):
                    if hasattr(subtable.ClassDef2, 'classDefs'):
                        for glyph in subtable.ClassDef2.classDefs.keys():
                            glyphs_gpos_count[glyph] += 1
    
    # Prepare glyph metrics CSV data
    # Get all unique glyph names from both glyf and hmtx to handle edge cases
    all_glyph_names = set(glyf.keys()) | set(hmtx.metrics.keys())
    
    glyph_rows = []
    glyph_data_dict = {}  # Dictionary for fast lookup by glyph_name
    for glyph_name in all_glyph_names:
        # Check if glyph exists in tables
        has_hmtx = glyph_name in hmtx.metrics
        has_vmtx = vmtx is not None and glyph_name in vmtx.metrics
        has_glyf = glyph_name in glyf
        cmap_used = glyphs_cmap_count[glyph_name]
        glyf_used = glyphs_glyf_count[glyph_name]
        gsub_used = glyphs_gsub_count[glyph_name]
        gpos_used = glyphs_gpos_count[glyph_name]
        
        # Get horizontal metrics
        advance_width = None
        lsb = None
        if has_hmtx:
            advance_width, lsb = hmtx.metrics[glyph_name]
        
        # Get glyph bounding box
        xMin, yMin, xMax, yMax = None, None, None, None
        is_composite = None
        num_contours = None
        
        if has_glyf:
            glyph = glyf[glyph_name]
            is_composite = glyph.isComposite()
            
            if hasattr(glyph, 'xMin'):
                xMin = glyph.xMin
                yMin = glyph.yMin
                xMax = glyph.xMax
                yMax = glyph.yMax
            
            if hasattr(glyph, 'numberOfContours'):
                num_contours = glyph.numberOfContours
        
        # Determine if glyph is empty (no contours or no bounding box)
        is_empty_glyph = (num_contours == 0) or (xMin is None)
        
        # Calculate width_unit
        width_unit = calculate_width_unit(advance_width, reference_width)
        
        # Get number of glyphs this glyph references
        num_glyph = glyph_num_refs[glyph_name]
        
        # Build glyph data
        glyph_data = {
            'glyph_name': glyph_name,
            'advance_width': advance_width,
            'lsb': lsb,
            'xMin': xMin,
            'yMin': yMin,
            'xMax': xMax,
            'yMax': yMax,
            'width': (xMax - xMin) if (xMin is not None and xMax is not None) else None,
            'height': (yMax - yMin) if (yMin is not None and yMax is not None) else None,
            'width_unit': width_unit,
            'is_empty_glyph': is_empty_glyph,
            'is_composite': is_composite,
            'num_contours': num_contours,
            'num_glyph': num_glyph,
            'cmap_used': cmap_used,
            'glyf_used': glyf_used,
            'gsub_used': gsub_used,
            'gpos_used': gpos_used,
            'has_glyf': has_glyf,
            'has_hmtx': has_hmtx,
            'has_vmtx': has_vmtx,
        }
        glyph_rows.append(glyph_data)
        glyph_data_dict[glyph_name] = glyph_data
    
    # Prepare codepoint mapping CSV data (with glyph metrics included)
    codepoint_rows = []
    for codepoint in sorted(cmap.keys()):
        glyph_name = cmap[codepoint]
        # Start with codepoint info
        row = {
            'codepoint': f"U+{codepoint:04X}",
            'codepoint_dec': codepoint,
            'glyph_name': glyph_name,
        }
        # Add glyph metrics if available
        if glyph_name in glyph_data_dict:
            glyph_data = glyph_data_dict[glyph_name]
            row.update({
                'advance_width': glyph_data['advance_width'],
                'lsb': glyph_data['lsb'],
                'xMin': glyph_data['xMin'],
                'yMin': glyph_data['yMin'],
                'xMax': glyph_data['xMax'],
                'yMax': glyph_data['yMax'],
                'width': glyph_data['width'],
                'height': glyph_data['height'],
                'width_unit': glyph_data['width_unit'],
                'is_empty_glyph': glyph_data['is_empty_glyph'],
                'is_composite': glyph_data['is_composite'],
                'num_contours': glyph_data['num_contours'],
                'num_glyph': glyph_data['num_glyph'],
                'cmap_used': glyph_data['cmap_used'],
                'glyf_used': glyph_data['glyf_used'],
                'gsub_used': glyph_data['gsub_used'],
                'gpos_used': glyph_data['gpos_used'],
                'has_glyf': glyph_data['has_glyf'],
                'has_hmtx': glyph_data['has_hmtx'],
                'has_vmtx': glyph_data['has_vmtx'],
            })
        codepoint_rows.append(row)
    
    # Track which glyphs are used in GSUB table
    glyphs_gsub_count = Counter()
    gsub = font.get('GSUB')
    if gsub and hasattr(gsub, 'table'):
        for lookup in gsub.table.LookupList.Lookup:
            for subtable in lookup.SubTable:
                # Collect glyphs from various GSUB subtable types
                if hasattr(subtable, 'mapping'):
                    for key in subtable.mapping.keys():
                        glyphs_gsub_count[key] += 1
                    for value in subtable.mapping.values():
                        if isinstance(value, list):
                            for glyph in value:
                                glyphs_gsub_count[glyph] += 1
                        else:
                            glyphs_gsub_count[value] += 1
                if hasattr(subtable, 'ligatures'):
                    for glyph_name, ligatures in subtable.ligatures.items():
                        glyphs_gsub_count[glyph_name] += 1
                        for ligature in ligatures:
                            glyphs_gsub_count[ligature.LigGlyph] += 1
                            for comp in ligature.Component:
                                glyphs_gsub_count[comp] += 1
                if hasattr(subtable, 'alternates'):
                    for glyph_name, alts in subtable.alternates.items():
                        glyphs_gsub_count[glyph_name] += 1
                        for alt in alts:
                            glyphs_gsub_count[alt] += 1
                if hasattr(subtable, 'Coverage'):
                    if hasattr(subtable.Coverage, 'glyphs'):
                        for glyph in subtable.Coverage.glyphs:
                            glyphs_gsub_count[glyph] += 1
    
    # Track which glyphs are used in GPOS table
    glyphs_gpos_count = Counter()
    gpos = font.get('GPOS')
    if gpos and hasattr(gpos, 'table'):
        for lookup in gpos.table.LookupList.Lookup:
            for subtable in lookup.SubTable:
                # Collect glyphs from various GPOS subtable types
                if hasattr(subtable, 'Coverage'):
                    if hasattr(subtable.Coverage, 'glyphs'):
                        for glyph in subtable.Coverage.glyphs:
                            glyphs_gpos_count[glyph] += 1
                if hasattr(subtable, 'ClassDef1'):
                    if hasattr(subtable.ClassDef1, 'classDefs'):
                        for glyph in subtable.ClassDef1.classDefs.keys():
                            glyphs_gpos_count[glyph] += 1
                if hasattr(subtable, 'ClassDef2'):
                    if hasattr(subtable.ClassDef2, 'classDefs'):
                        for glyph in subtable.ClassDef2.classDefs.keys():
                            glyphs_gpos_count[glyph] += 1
    
    # Sort glyph rows by glyph_name for consistent output
    glyph_rows.sort(key=lambda x: x['glyph_name'])
    
    # Sort glyphref rows by ref_from, then ref_to
    glyphref_rows.sort(key=lambda x: (x['ref_from'], x['ref_to']))
    
    # Write codepoint CSV
    codepoint_fieldnames = [
        'codepoint',
        'codepoint_dec',
        'glyph_name',
        'advance_width',
        'lsb',
        'xMin',
        'yMin',
        'xMax',
        'yMax',
        'width',
        'height',
        'width_unit',
        'is_empty_glyph',
        'is_composite',
        'num_contours',
        'num_glyph',
        'cmap_used',
        'glyf_used',
        'gsub_used',
        'gpos_used',
        'has_glyf',
        'has_hmtx',
        'has_vmtx',
    ]
    
    try:
        with open(output_codepoint_csv, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=codepoint_fieldnames)
            writer.writeheader()
            writer.writerows(codepoint_rows)
        
        print(f"Successfully wrote {len(codepoint_rows)} codepoints to {output_codepoint_csv}")
    except Exception as e:
        print(f"Error writing codepoint CSV file: {e}", file=sys.stderr)
        sys.exit(1)
    
    # Write glyph CSV
    glyph_fieldnames = [
        'glyph_name',
        'advance_width',
        'lsb',
        'xMin',
        'yMin',
        'xMax',
        'yMax',
        'width',
        'height',
        'width_unit',
        'is_empty_glyph',
        'is_composite',
        'num_contours',
        'num_glyph',
        'cmap_used',
        'glyf_used',
        'gsub_used',
        'gpos_used',
        'has_glyf',
        'has_hmtx',
        'has_vmtx',
    ]
    
    try:
        with open(output_glyph_csv, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=glyph_fieldnames)
            writer.writeheader()
            writer.writerows(glyph_rows)
        
        print(f"Successfully wrote {len(glyph_rows)} glyphs to {output_glyph_csv}")
    except Exception as e:
        print(f"Error writing glyph CSV file: {e}", file=sys.stderr)
        sys.exit(1)
    
    # Write glyphref CSV
    glyphref_fieldnames = ['ref_from', 'ref_to']
    
    try:
        with open(output_glyphref_csv, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=glyphref_fieldnames)
            writer.writeheader()
            writer.writerows(glyphref_rows)
        
        print(f"Successfully wrote {len(glyphref_rows)} glyph references to {output_glyphref_csv}")
    except Exception as e:
        print(f"Error writing glyphref CSV file: {e}", file=sys.stderr)
        sys.exit(1)
    
    font.close()


def main():
    parser = argparse.ArgumentParser(
        description="Dump TTF character information to CSV files."
    )
    parser.add_argument(
        "input_ttf",
        help="Path to input TTF file"
    )
    parser.add_argument(
        "output_codepoint_csv",
        help="Path to output codepoint mapping CSV file"
    )
    parser.add_argument(
        "output_glyph_csv",
        help="Path to output glyph metrics CSV file"
    )
    parser.add_argument(
        "output_glyphref_csv",
        help="Path to output glyph reference relationship CSV file"
    )
    
    args = parser.parse_args()
    dump_font_to_csv(args.input_ttf, args.output_codepoint_csv, args.output_glyph_csv, args.output_glyphref_csv)


if __name__ == "__main__":
    main()
