#!/usr/bin/env python3
"""
Dump GPOS features from TTF font to CSV file.
Extracts all GPOS feature information including tags, indices, and associated scripts.
"""
import argparse
import csv
import sys
from fontTools.ttLib import TTFont


def extract_gpos_features(font):
    """
    Extract GPOS feature information from font.
    
    Returns:
        List of dictionaries containing feature information
    """
    if 'GPOS' not in font:
        return []
    
    gpos = font['GPOS']
    if not hasattr(gpos, 'table'):
        return []
    
    table = gpos.table
    features = []
    
    # Extract features from FeatureList
    if hasattr(table, 'FeatureList') and table.FeatureList:
        feature_records = table.FeatureList.FeatureRecord
        
        for idx, feature_record in enumerate(feature_records):
            feature_tag = str(feature_record.FeatureTag)
            feature = feature_record.Feature
            
            # Get associated scripts
            scripts = []
            if hasattr(table, 'ScriptList') and table.ScriptList:
                for script_record in table.ScriptList.ScriptRecord:
                    script_tag = str(script_record.ScriptTag)
                    script = script_record.Script
                    
                    # Check DefaultLangSys
                    if hasattr(script, 'DefaultLangSys') and script.DefaultLangSys:
                        if idx in script.DefaultLangSys.FeatureIndex:
                            scripts.append(f"{script_tag}:dflt")
                    
                    # Check other LangSys
                    if hasattr(script, 'LangSysRecord'):
                        for lang_record in script.LangSysRecord:
                            lang_tag = str(lang_record.LangSysTag)
                            if idx in lang_record.LangSys.FeatureIndex:
                                scripts.append(f"{script_tag}:{lang_tag}")
            
            # Get lookup indices
            lookup_indices = []
            if hasattr(feature, 'LookupListIndex'):
                lookup_indices = list(feature.LookupListIndex)
            
            # Get lookup count
            lookup_count = len(lookup_indices)
            
            features.append({
                'feature_index': idx,
                'feature_tag': feature_tag,
                'lookup_count': lookup_count,
                'lookup_indices': ','.join(map(str, lookup_indices)),
                'scripts': ';'.join(scripts) if scripts else '',
                'num_scripts': len(scripts),
            })
    
    return features


def dump_gpos_features_csv(input_ttf, output_csv, font_index=0):
    """
    Extract GPOS features and write to CSV file.
    
    Args:
        input_ttf: Path to input TTF/TTC file
        output_csv: Path to output CSV file
        font_index: Index of font to use (for TTC files, default 0)
    """
    try:
        font = TTFont(input_ttf, fontNumber=font_index)
    except Exception as e:
        print(f"Error loading font: {e}", file=sys.stderr)
        sys.exit(1)
    
    features = extract_gpos_features(font)
    font.close()
    
    if not features:
        print(f"No GPOS features found in {input_ttf}", file=sys.stderr)
        sys.exit(1)
    
    # Write CSV
    fieldnames = [
        'feature_index',
        'feature_tag',
        'lookup_count',
        'lookup_indices',
        'num_scripts',
        'scripts',
    ]
    
    with open(output_csv, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(features)
    
    print(f"GPOS features written to {output_csv}")
    print(f"Total features: {len(features)}")


def main():
    parser = argparse.ArgumentParser(
        description='Dump GPOS features from TTF/TTC font to CSV file.'
    )
    parser.add_argument(
        'input_ttf',
        help='Path to input TTF/TTC file'
    )
    parser.add_argument(
        'output_csv',
        help='Path to output CSV file'
    )
    parser.add_argument(
        '--font-index', '-i',
        type=int,
        default=0,
        help='Font index for TTC files (default: 0)'
    )
    
    args = parser.parse_args()
    dump_gpos_features_csv(args.input_ttf, args.output_csv, args.font_index)


if __name__ == '__main__':
    main()
