#!/usr/bin/env python3
"""
Dump GSUB lookups from TTF font to CSV file.
Extracts all GSUB lookup information including type, flags, and subtable count.
"""
import argparse
import csv
import sys
from fontTools.ttLib import TTFont


def extract_gsub_lookups(font):
    """
    Extract GSUB lookup information from font.
    
    Returns:
        List of dictionaries containing lookup information
    """
    if 'GSUB' not in font:
        return []
    
    gsub = font['GSUB']
    if not hasattr(gsub, 'table'):
        return []
    
    table = gsub.table
    lookups = []
    
    # Extract lookups from LookupList
    if hasattr(table, 'LookupList') and table.LookupList:
        lookup_list = table.LookupList.Lookup
        
        for idx, lookup in enumerate(lookup_list):
            # Get lookup type
            lookup_type = getattr(lookup, 'LookupType', None)
            
            # Get lookup flag
            lookup_flag = getattr(lookup, 'LookupFlag', None)
            
            # Get subtable count
            subtable_count = len(lookup.SubTable) if hasattr(lookup, 'SubTable') else 0
            
            # Get mark filtering set (if any)
            mark_filtering_set = getattr(lookup, 'MarkFilteringSet', None)
            
            lookups.append({
                'lookup_index': idx,
                'lookup_type': lookup_type,
                'lookup_flag': lookup_flag,
                'subtable_count': subtable_count,
                'mark_filtering_set': mark_filtering_set if mark_filtering_set is not None else '',
            })
    
    return lookups


def dump_gsub_lookups_csv(input_ttf, output_csv, font_index=0):
    """
    Extract GSUB lookups and write to CSV file.
    
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
    
    lookups = extract_gsub_lookups(font)
    font.close()
    
    if not lookups:
        print(f"No GSUB lookups found in {input_ttf}", file=sys.stderr)
        sys.exit(1)
    
    # Write CSV
    fieldnames = [
        'lookup_index',
        'lookup_type',
        'lookup_flag',
        'subtable_count',
        'mark_filtering_set',
    ]
    
    with open(output_csv, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(lookups)
    
    print(f"GSUB lookups written to {output_csv}")
    print(f"Total lookups: {len(lookups)}")


def main():
    parser = argparse.ArgumentParser(
        description='Dump GSUB lookups from TTF/TTC font to CSV file.'
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
    dump_gsub_lookups_csv(args.input_ttf, args.output_csv, args.font_index)


if __name__ == '__main__':
    main()
