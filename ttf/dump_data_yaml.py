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
    result = {}
    
    # Dynamically capture all head table attributes
    for attr_name in dir(head):
        if attr_name.startswith('_') or callable(getattr(head, attr_name)):
            continue
        
        try:
            attr_value = getattr(head, attr_name)
            
            # Convert specific types for better readability
            if attr_name in ['created', 'modified']:
                result[attr_name] = str(attr_value)
            elif attr_name in ['magicNumber', 'checkSumAdjustment']:
                result[attr_name] = hex(attr_value)
            elif attr_name == 'fontRevision':
                result[attr_name] = round(attr_value, 4)
            else:
                result[attr_name] = attr_value
        except Exception:
            pass
    
    return result


def dump_hhea_table(font):
    """Extract hhea (horizontal header) table information."""
    if 'hhea' not in font:
        return None
    
    hhea = font['hhea']
    result = {}
    
    # Dynamically capture all hhea table attributes
    for attr_name in dir(hhea):
        if attr_name.startswith('_') or callable(getattr(hhea, attr_name)):
            continue
        
        try:
            result[attr_name] = getattr(hhea, attr_name)
        except Exception:
            pass
    
    return result


def dump_os2_table(font):
    """Extract OS/2 table information."""
    if 'OS/2' not in font:
        return None
    
    os2 = font['OS/2']
    result = {}
    
    # Dynamically capture all OS/2 attributes
    for attr_name in dir(os2):
        # Skip private/internal attributes and methods
        if attr_name.startswith('_') or callable(getattr(os2, attr_name)):
            continue
        
        try:
            attr_value = getattr(os2, attr_name)
            
            # Handle special cases
            if attr_name == 'panose':
                # Panose classification - expand its sub-attributes
                result['panose'] = {}
                for panose_attr in dir(attr_value):
                    if not panose_attr.startswith('_') and not callable(getattr(attr_value, panose_attr)):
                        result['panose'][panose_attr] = getattr(attr_value, panose_attr)
            elif isinstance(attr_value, int) and attr_value > 0xFFFF:
                # Convert large integers to hex for readability (like unicode/codepage ranges)
                result[attr_name] = hex(attr_value)
            else:
                # Store the value as-is
                result[attr_name] = attr_value
        except Exception:
            # Skip attributes that can't be accessed
            pass
    
    return result


def dump_post_table(font):
    """Extract post table information."""
    if 'post' not in font:
        return None
    
    post = font['post']
    result = {}
    
    # Dynamically capture all post table attributes
    for attr_name in dir(post):
        if attr_name.startswith('_') or callable(getattr(post, attr_name)):
            continue
        
        try:
            result[attr_name] = getattr(post, attr_name)
        except Exception:
            pass
    
    return result


def dump_maxp_table(font):
    """Extract maxp table information."""
    if 'maxp' not in font:
        return None
    
    maxp = font['maxp']
    result = {}
    
    # Dynamically capture all maxp table attributes
    for attr_name in dir(maxp):
        if attr_name.startswith('_') or callable(getattr(maxp, attr_name)):
            continue
        
        try:
            attr_value = getattr(maxp, attr_name)
            
            # Convert tableVersion to string for consistency
            if attr_name == 'tableVersion':
                result[attr_name] = str(attr_value)
            else:
                result[attr_name] = attr_value
        except Exception:
            pass
    
    return result


def dump_vhea_table(font):
    """Extract vhea (vertical header) table information."""
    if 'vhea' not in font:
        return None
    
    vhea = font['vhea']
    result = {}
    
    # Dynamically capture all vhea table attributes
    for attr_name in dir(vhea):
        if attr_name.startswith('_') or callable(getattr(vhea, attr_name)):
            continue
        
        try:
            result[attr_name] = getattr(vhea, attr_name)
        except Exception:
            pass
    
    return result


def dump_gasp_table(font):
    """Extract gasp table information."""
    if 'gasp' not in font:
        return None
    
    gasp = font['gasp']
    result = {}
    
    # Dynamically capture all gasp table attributes
    for attr_name in dir(gasp):
        if attr_name.startswith('_') or callable(getattr(gasp, attr_name)):
            continue
        
        try:
            attr_value = getattr(gasp, attr_name)
            
            # Convert gaspRange dict keys to strings for YAML compatibility
            if attr_name == 'gaspRange' and isinstance(attr_value, dict):
                result[attr_name] = {str(k): v for k, v in attr_value.items()}
            else:
                result[attr_name] = attr_value
        except Exception:
            pass
    
    return result


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
    result = {}
    
    # Dynamically capture all kern table attributes
    for attr_name in dir(kern):
        if attr_name.startswith('_') or callable(getattr(kern, attr_name)):
            continue
        
        try:
            attr_value = getattr(kern, attr_name)
            
            # Handle special cases
            if attr_name == 'kernTables' and hasattr(attr_value, '__len__'):
                result['num_subtables'] = len(attr_value)
                total_pairs = 0
                for subtable in attr_value:
                    if hasattr(subtable, 'kernTable'):
                        total_pairs += len(subtable.kernTable)
                result['total_kern_pairs'] = total_pairs
            else:
                result[attr_name] = attr_value
        except Exception:
            pass
    
    return result


def dump_gdef_table(font):
    """Extract GDEF table summary."""
    if 'GDEF' not in font:
        return None
    
    gdef = font['GDEF']
    result = {}
    
    # Dynamically capture all GDEF table attributes
    for attr_name in dir(gdef):
        if attr_name.startswith('_') or callable(getattr(gdef, attr_name)):
            continue
        
        try:
            attr_value = getattr(gdef, attr_name)
            
            # Handle nested table object
            if attr_name == 'table' and hasattr(attr_value, '__dict__'):
                result['table_info'] = {}
                for sub_attr in dir(attr_value):
                    if sub_attr.startswith('_') or callable(getattr(attr_value, sub_attr)):
                        continue
                    try:
                        sub_value = getattr(attr_value, sub_attr)
                        # Convert Version to string
                        if sub_attr == 'Version':
                            result['table_info'][sub_attr] = str(sub_value)
                        # For complex objects, just note their presence
                        elif isinstance(sub_value, (str, int, float, bool, type(None))):
                            result['table_info'][sub_attr] = sub_value
                        elif sub_value:
                            result['table_info'][f'has_{sub_attr}'] = True
                    except Exception:
                        pass
            elif isinstance(attr_value, (str, int, float, bool, type(None), list)):
                result[attr_name] = attr_value
        except Exception:
            pass
    
    return result if result else None


def dump_gpos_table(font):
    """Extract GPOS table summary."""
    if 'GPOS' not in font:
        return None
    
    gpos = font['GPOS']
    result = {}
    
    # Dynamically capture all GPOS table attributes
    for attr_name in dir(gpos):
        if attr_name.startswith('_') or callable(getattr(gpos, attr_name)):
            continue
        
        try:
            attr_value = getattr(gpos, attr_name)
            
            # Handle nested table object
            if attr_name == 'table' and hasattr(attr_value, '__dict__'):
                result['table_info'] = {}
                for sub_attr in dir(attr_value):
                    if sub_attr.startswith('_') or callable(getattr(attr_value, sub_attr)):
                        continue
                    try:
                        sub_value = getattr(attr_value, sub_attr)
                        if sub_attr == 'Version':
                            result['table_info']['version'] = str(sub_value)
                        elif sub_attr == 'ScriptList' and sub_value and hasattr(sub_value, 'ScriptRecord'):
                            result['table_info']['num_scripts'] = len(sub_value.ScriptRecord)
                            result['table_info']['scripts'] = [str(rec.ScriptTag) for rec in sub_value.ScriptRecord]
                        elif sub_attr == 'FeatureList' and sub_value and hasattr(sub_value, 'FeatureRecord'):
                            result['table_info']['num_features'] = len(sub_value.FeatureRecord)
                            # features list hidden - use dump_gpos_feature_csv.py to extract
                        elif sub_attr == 'LookupList' and sub_value and hasattr(sub_value, 'Lookup'):
                            result['table_info']['num_lookups'] = len(sub_value.Lookup)
                        elif isinstance(sub_value, (str, int, float, bool, type(None))):
                            result['table_info'][sub_attr] = sub_value
                        elif sub_value:
                            result['table_info'][f'has_{sub_attr}'] = True
                    except Exception:
                        pass
            elif isinstance(attr_value, (str, int, float, bool, type(None), list)):
                result[attr_name] = attr_value
        except Exception:
            pass
    
    return result if result else None


def dump_gsub_table(font):
    """Extract GSUB table summary."""
    if 'GSUB' not in font:
        return None
    
    gsub = font['GSUB']
    result = {}
    
    # Dynamically capture all GSUB table attributes
    for attr_name in dir(gsub):
        if attr_name.startswith('_') or callable(getattr(gsub, attr_name)):
            continue
        
        try:
            attr_value = getattr(gsub, attr_name)
            
            # Handle nested table object
            if attr_name == 'table' and hasattr(attr_value, '__dict__'):
                result['table_info'] = {}
                for sub_attr in dir(attr_value):
                    if sub_attr.startswith('_') or callable(getattr(attr_value, sub_attr)):
                        continue
                    try:
                        sub_value = getattr(attr_value, sub_attr)
                        if sub_attr == 'Version':
                            result['table_info']['version'] = str(sub_value)
                        elif sub_attr == 'ScriptList' and sub_value and hasattr(sub_value, 'ScriptRecord'):
                            result['table_info']['num_scripts'] = len(sub_value.ScriptRecord)
                            result['table_info']['scripts'] = [str(rec.ScriptTag) for rec in sub_value.ScriptRecord]
                        elif sub_attr == 'FeatureList' and sub_value and hasattr(sub_value, 'FeatureRecord'):
                            result['table_info']['num_features'] = len(sub_value.FeatureRecord)
                            # features list hidden - use dump_gsub_feature_csv.py to extract
                        elif sub_attr == 'LookupList' and sub_value and hasattr(sub_value, 'Lookup'):
                            result['table_info']['num_lookups'] = len(sub_value.Lookup)
                        elif isinstance(sub_value, (str, int, float, bool, type(None))):
                            result['table_info'][sub_attr] = sub_value
                        elif sub_value:
                            result['table_info'][f'has_{sub_attr}'] = True
                    except Exception:
                        pass
            elif isinstance(attr_value, (str, int, float, bool, type(None), list)):
                result[attr_name] = attr_value
        except Exception:
            pass
    
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
