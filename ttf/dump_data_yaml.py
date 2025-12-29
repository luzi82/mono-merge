#!/usr/bin/env python3
"""
Dump TTF font metadata to YAML file.
Outputs comprehensive font information excluding per-character data.
"""
import argparse
import sys
import yaml
from fontTools.ttLib import TTFont


def get_name_record(name_table, name_id):
    """Get a name record value by ID, preferring Unicode/Windows platforms."""
    if not name_table:
        return None
    for record in name_table.names:
        if record.nameID == name_id:
            try:
                return record.toUnicode()
            except Exception:
                pass
    return None


def dump_name_table(font):
    """Extract all name table entries."""
    if 'name' not in font:
        return None
    
    name_table = font['name']
    name_ids = {
        0: 'copyright',
        1: 'family_name',
        2: 'subfamily_name',
        3: 'unique_id',
        4: 'full_name',
        5: 'version',
        6: 'postscript_name',
        7: 'trademark',
        8: 'manufacturer',
        9: 'designer',
        10: 'description',
        11: 'vendor_url',
        12: 'designer_url',
        13: 'license',
        14: 'license_url',
        16: 'typographic_family_name',
        17: 'typographic_subfamily_name',
        18: 'compatible_full_name',
        19: 'sample_text',
        21: 'wws_family_name',
        22: 'wws_subfamily_name',
    }
    
    result = {}
    for name_id, name_key in name_ids.items():
        value = get_name_record(name_table, name_id)
        if value:
            result[name_key] = value
    
    return result if result else None


def dump_head_table(font):
    """Extract head table information."""
    if 'head' not in font:
        return None
    
    head = font['head']
    return {
        'units_per_em': head.unitsPerEm,
        'created': str(head.created) if hasattr(head, 'created') else None,
        'modified': str(head.modified) if hasattr(head, 'modified') else None,
        'x_min': head.xMin,
        'y_min': head.yMin,
        'x_max': head.xMax,
        'y_max': head.yMax,
        'mac_style': head.macStyle,
        'lowest_rec_ppem': head.lowestRecPPEM,
        'font_direction_hint': head.fontDirectionHint,
        'index_to_loc_format': head.indexToLocFormat,
        'glyph_data_format': head.glyphDataFormat,
        'flags': head.flags,
        'font_revision': round(head.fontRevision, 4),
        'magic_number': hex(head.magicNumber),
        'checksum_adjustment': hex(head.checkSumAdjustment),
    }


def dump_hhea_table(font):
    """Extract hhea (horizontal header) table information."""
    if 'hhea' not in font:
        return None
    
    hhea = font['hhea']
    return {
        'ascender': hhea.ascent,
        'descender': hhea.descent,
        'line_gap': hhea.lineGap,
        'advance_width_max': hhea.advanceWidthMax,
        'min_left_side_bearing': hhea.minLeftSideBearing,
        'min_right_side_bearing': hhea.minRightSideBearing,
        'x_max_extent': hhea.xMaxExtent,
        'caret_slope_rise': hhea.caretSlopeRise,
        'caret_slope_run': hhea.caretSlopeRun,
        'caret_offset': hhea.caretOffset,
        'number_of_h_metrics': hhea.numberOfHMetrics,
    }


def dump_os2_table(font):
    """Extract OS/2 table information."""
    if 'OS/2' not in font:
        return None
    
    os2 = font['OS/2']
    result = {
        'version': os2.version,
        'x_avg_char_width': os2.xAvgCharWidth,
        'us_weight_class': os2.usWeightClass,
        'us_width_class': os2.usWidthClass,
        'fs_type': os2.fsType,
        'y_subscript_x_size': os2.ySubscriptXSize,
        'y_subscript_y_size': os2.ySubscriptYSize,
        'y_subscript_x_offset': os2.ySubscriptXOffset,
        'y_subscript_y_offset': os2.ySubscriptYOffset,
        'y_superscript_x_size': os2.ySuperscriptXSize,
        'y_superscript_y_size': os2.ySuperscriptYSize,
        'y_superscript_x_offset': os2.ySuperscriptXOffset,
        'y_superscript_y_offset': os2.ySuperscriptYOffset,
        'y_strikeout_size': os2.yStrikeoutSize,
        'y_strikeout_position': os2.yStrikeoutPosition,
        's_family_class': os2.sFamilyClass,
        's_typo_ascender': os2.sTypoAscender,
        's_typo_descender': os2.sTypoDescender,
        's_typo_line_gap': os2.sTypoLineGap,
        'us_win_ascent': os2.usWinAscent,
        'us_win_descent': os2.usWinDescent,
        'fs_selection': os2.fsSelection,
        'us_first_char_index': os2.usFirstCharIndex,
        'us_last_char_index': os2.usLastCharIndex,
        's_x_height': getattr(os2, 'sxHeight', None),
        's_cap_height': getattr(os2, 'sCapHeight', None),
        'us_default_char': getattr(os2, 'usDefaultChar', None),
        'us_break_char': getattr(os2, 'usBreakChar', None),
        'us_max_context': getattr(os2, 'usMaxContext', None),
    }
    
    # Panose classification
    if hasattr(os2, 'panose'):
        panose = os2.panose
        result['panose'] = {
            'b_family_type': panose.bFamilyType,
            'b_serif_style': panose.bSerifStyle,
            'b_weight': panose.bWeight,
            'b_proportion': panose.bProportion,
            'b_contrast': panose.bContrast,
            'b_stroke_variation': panose.bStrokeVariation,
            'b_arm_style': panose.bArmStyle,
            'b_letterform': panose.bLetterForm,
            'b_midline': panose.bMidline,
            'b_x_height': panose.bXHeight,
        }
    
    # Unicode ranges (if available)
    if hasattr(os2, 'ulUnicodeRange1'):
        result['unicode_ranges'] = {
            'range1': hex(os2.ulUnicodeRange1),
            'range2': hex(os2.ulUnicodeRange2),
            'range3': hex(os2.ulUnicodeRange3),
            'range4': hex(os2.ulUnicodeRange4),
        }
    
    # Code page ranges (if available)
    if hasattr(os2, 'ulCodePageRange1'):
        result['code_page_ranges'] = {
            'range1': hex(os2.ulCodePageRange1),
            'range2': hex(os2.ulCodePageRange2),
        }
    
    return result


def dump_post_table(font):
    """Extract post table information."""
    if 'post' not in font:
        return None
    
    post = font['post']
    return {
        'format_type': post.formatType,
        'italic_angle': post.italicAngle,
        'underline_position': post.underlinePosition,
        'underline_thickness': post.underlineThickness,
        'is_fixed_pitch': post.isFixedPitch,
        'min_mem_type42': post.minMemType42,
        'max_mem_type42': post.maxMemType42,
        'min_mem_type1': post.minMemType1,
        'max_mem_type1': post.maxMemType1,
    }


def dump_maxp_table(font):
    """Extract maxp table information."""
    if 'maxp' not in font:
        return None
    
    maxp = font['maxp']
    result = {
        'num_glyphs': maxp.numGlyphs,
    }
    
    # Version if available
    if hasattr(maxp, 'tableVersion'):
        result['version'] = str(maxp.tableVersion)
    
    # TrueType-specific fields (version 1.0)
    if hasattr(maxp, 'maxPoints'):
        result.update({
            'max_points': maxp.maxPoints,
            'max_contours': maxp.maxContours,
            'max_composite_points': maxp.maxCompositePoints,
            'max_composite_contours': maxp.maxCompositeContours,
            'max_zones': maxp.maxZones,
            'max_twilight_points': maxp.maxTwilightPoints,
            'max_storage': maxp.maxStorage,
            'max_function_defs': maxp.maxFunctionDefs,
            'max_instruction_defs': maxp.maxInstructionDefs,
            'max_stack_elements': maxp.maxStackElements,
            'max_size_of_instructions': maxp.maxSizeOfInstructions,
            'max_component_elements': maxp.maxComponentElements,
            'max_component_depth': maxp.maxComponentDepth,
        })
    
    return result


def dump_vhea_table(font):
    """Extract vhea (vertical header) table information."""
    if 'vhea' not in font:
        return None
    
    vhea = font['vhea']
    return {
        'ascent': vhea.ascent,
        'descent': vhea.descent,
        'line_gap': vhea.lineGap,
        'advance_height_max': vhea.advanceHeightMax,
        'min_top_side_bearing': vhea.minTopSideBearing,
        'min_bottom_side_bearing': vhea.minBottomSideBearing,
        'y_max_extent': vhea.yMaxExtent,
        'caret_slope_rise': vhea.caretSlopeRise,
        'caret_slope_run': vhea.caretSlopeRun,
        'caret_offset': vhea.caretOffset,
        'number_of_v_metrics': vhea.numberOfVMetrics,
    }


def dump_gasp_table(font):
    """Extract gasp table information."""
    if 'gasp' not in font:
        return None
    
    gasp = font['gasp']
    return {
        'version': gasp.version,
        'gasp_ranges': {str(k): v for k, v in gasp.gaspRange.items()},
    }


def dump_cmap_info(font):
    """Extract cmap table summary (not per-character data)."""
    if 'cmap' not in font:
        return None
    
    cmap = font['cmap']
    tables = []
    for table in cmap.tables:
        tables.append({
            'platform_id': table.platformID,
            'plat_enc_id': table.platEncID,
            'format': table.format,
            'is_unicode': table.isUnicode(),
            'language': getattr(table, 'language', None),
            'num_chars': len(table.cmap) if hasattr(table, 'cmap') else None,
        })
    
    best_cmap = font.getBestCmap()
    return {
        'tables': tables,
        'best_cmap_size': len(best_cmap) if best_cmap else 0,
    }


def dump_glyph_summary(font):
    """Extract glyph summary (not per-character data)."""
    glyph_order = font.getGlyphOrder()
    
    result = {
        'total_glyphs': len(glyph_order),
        'first_10_glyphs': glyph_order[:10],
        'last_10_glyphs': glyph_order[-10:] if len(glyph_order) > 10 else glyph_order,
    }
    
    # Count generic glyph names
    generic_count = sum(1 for name in glyph_order if name.startswith('glyph'))
    if generic_count > 0:
        result['generic_glyph_count'] = generic_count
    
    return result


def dump_table_list(font):
    """Get list of all tables in the font."""
    return sorted([str(t) for t in font.keys()])


def dump_cvt_table(font):
    """Extract cvt (control value table) summary."""
    if 'cvt ' not in font:
        return None
    
    cvt = font['cvt ']
    return {
        'num_values': len(cvt.values) if hasattr(cvt, 'values') else 0,
    }


def dump_fpgm_table(font):
    """Extract fpgm (font program) summary."""
    if 'fpgm' not in font:
        return None
    
    fpgm = font['fpgm']
    program = fpgm.program
    return {
        'program_length': len(program.getAssembly()) if hasattr(program, 'getAssembly') else 0,
    }


def dump_prep_table(font):
    """Extract prep (control value program) summary."""
    if 'prep' not in font:
        return None
    
    prep = font['prep']
    program = prep.program
    return {
        'program_length': len(program.getAssembly()) if hasattr(program, 'getAssembly') else 0,
    }


def dump_kern_table(font):
    """Extract kern table summary."""
    if 'kern' not in font:
        return None
    
    kern = font['kern']
    result = {
        'version': kern.version,
    }
    
    if hasattr(kern, 'kernTables'):
        result['num_subtables'] = len(kern.kernTables)
        total_pairs = 0
        for subtable in kern.kernTables:
            if hasattr(subtable, 'kernTable'):
                total_pairs += len(subtable.kernTable)
        result['total_kern_pairs'] = total_pairs
    
    return result


def dump_gdef_table(font):
    """Extract GDEF table summary."""
    if 'GDEF' not in font:
        return None
    
    gdef = font['GDEF']
    result = {}
    
    if hasattr(gdef.table, 'Version'):
        result['version'] = str(gdef.table.Version)
    
    if hasattr(gdef.table, 'GlyphClassDef') and gdef.table.GlyphClassDef:
        result['has_glyph_class_def'] = True
    
    if hasattr(gdef.table, 'AttachList') and gdef.table.AttachList:
        result['has_attach_list'] = True
    
    if hasattr(gdef.table, 'LigCaretList') and gdef.table.LigCaretList:
        result['has_lig_caret_list'] = True
    
    if hasattr(gdef.table, 'MarkAttachClassDef') and gdef.table.MarkAttachClassDef:
        result['has_mark_attach_class_def'] = True
    
    if hasattr(gdef.table, 'MarkGlyphSetsDef') and gdef.table.MarkGlyphSetsDef:
        result['has_mark_glyph_sets_def'] = True
    
    return result if result else None


def dump_gpos_table(font):
    """Extract GPOS table summary."""
    if 'GPOS' not in font:
        return None
    
    gpos = font['GPOS']
    result = {}
    
    if hasattr(gpos.table, 'Version'):
        result['version'] = str(gpos.table.Version)
    
    if hasattr(gpos.table, 'ScriptList') and gpos.table.ScriptList:
        result['num_scripts'] = len(gpos.table.ScriptList.ScriptRecord)
        result['scripts'] = [str(rec.ScriptTag) for rec in gpos.table.ScriptList.ScriptRecord]
    
    if hasattr(gpos.table, 'FeatureList') and gpos.table.FeatureList:
        result['num_features'] = len(gpos.table.FeatureList.FeatureRecord)
        result['features'] = [str(rec.FeatureTag) for rec in gpos.table.FeatureList.FeatureRecord]
    
    if hasattr(gpos.table, 'LookupList') and gpos.table.LookupList:
        result['num_lookups'] = len(gpos.table.LookupList.Lookup)
    
    return result if result else None


def dump_gsub_table(font):
    """Extract GSUB table summary."""
    if 'GSUB' not in font:
        return None
    
    gsub = font['GSUB']
    result = {}
    
    if hasattr(gsub.table, 'Version'):
        result['version'] = str(gsub.table.Version)
    
    if hasattr(gsub.table, 'ScriptList') and gsub.table.ScriptList:
        result['num_scripts'] = len(gsub.table.ScriptList.ScriptRecord)
        result['scripts'] = [str(rec.ScriptTag) for rec in gsub.table.ScriptList.ScriptRecord]
    
    if hasattr(gsub.table, 'FeatureList') and gsub.table.FeatureList:
        result['num_features'] = len(gsub.table.FeatureList.FeatureRecord)
        result['features'] = [str(rec.FeatureTag) for rec in gsub.table.FeatureList.FeatureRecord]
    
    if hasattr(gsub.table, 'LookupList') and gsub.table.LookupList:
        result['num_lookups'] = len(gsub.table.LookupList.Lookup)
    
    return result if result else None


def dump_font_data(input_ttf, output_yaml, font_index=0):
    """
    Extract font metadata and write to YAML file.
    
    Args:
        input_ttf: Path to input TTF/TTC file
        output_yaml: Path to output YAML file
        font_index: Index of font to use (for TTC files, default 0)
    """
    try:
        font = TTFont(input_ttf, fontNumber=font_index)
    except Exception as e:
        print(f"Error loading font: {e}", file=sys.stderr)
        sys.exit(1)
    
    data = {
        'file': input_ttf,
        'font_index': font_index,
        'tables': dump_table_list(font),
        'name': dump_name_table(font),
        'head': dump_head_table(font),
        'hhea': dump_hhea_table(font),
        'os2': dump_os2_table(font),
        'post': dump_post_table(font),
        'maxp': dump_maxp_table(font),
        'vhea': dump_vhea_table(font),
        'gasp': dump_gasp_table(font),
        'cmap': dump_cmap_info(font),
        'glyphs': dump_glyph_summary(font),
        'cvt': dump_cvt_table(font),
        'fpgm': dump_fpgm_table(font),
        'prep': dump_prep_table(font),
        'kern': dump_kern_table(font),
        'GDEF': dump_gdef_table(font),
        'GPOS': dump_gpos_table(font),
        'GSUB': dump_gsub_table(font),
    }
    
    # Remove None values
    data = {k: v for k, v in data.items() if v is not None}
    
    font.close()
    
    # Write YAML output
    with open(output_yaml, 'w', encoding='utf-8') as f:
        yaml.dump(data, f, default_flow_style=False, allow_unicode=True, sort_keys=False)
    
    print(f"Font metadata written to {output_yaml}")


def main():
    parser = argparse.ArgumentParser(
        description='Dump TTF/TTC font metadata to YAML file (excludes per-character data).'
    )
    parser.add_argument(
        'input_ttf',
        help='Path to input TTF/TTC file to inspect'
    )
    parser.add_argument(
        'output_yaml',
        help='Path to output YAML file'
    )
    parser.add_argument(
        '--font-index', '-i',
        type=int,
        default=0,
        help='Font index for TTC files (default: 0)'
    )
    
    args = parser.parse_args()
    dump_font_data(args.input_ttf, args.output_yaml, args.font_index)


if __name__ == '__main__':
    main()
