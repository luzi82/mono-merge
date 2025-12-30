#!/usr/bin/env python3

import argparse
from fontTools import ttLib


def replace_metadata(input_ttf, replace_from, replace_to, output_ttf):
    """
    Replace text in all metadata fields of a TTF font.
    
    Args:
        input_ttf: Path to input TTF file
        replace_from: Text to search for
        replace_to: Text to replace with
        output_ttf: Path to output TTF file
    """
    # Load the font
    font = ttLib.TTFont(input_ttf)
    
    # Process the 'name' table which contains font metadata
    if 'name' in font:
        name_table = font['name']
        
        # Iterate through all name records
        for record in name_table.names:
            # Get the string value
            try:
                original_string = record.toUnicode()
                
                # Replace text if found
                if replace_from in original_string:
                    new_string = original_string.replace(replace_from, replace_to)
                    record.string = new_string
                    print(f"Replaced in nameID {record.nameID} ({record.platformID},{record.platEncID},{record.langID})")
                    print(f"  From: {original_string}")
                    print(f"  To:   {new_string}")
            except Exception as e:
                # Some name records might have encoding issues, skip them
                print(f"Warning: Could not process nameID {record.nameID}: {e}")
                continue
    
    # Process CFF table if present (for OpenType fonts)
    if 'CFF ' in font:
        cff = font['CFF ']
        if hasattr(cff, 'cff'):
            for fontname in cff.cff.fontNames:
                top_dict = cff.cff[fontname]
                
                # Replace in various CFF metadata fields
                if hasattr(top_dict, 'FullName') and top_dict.FullName:
                    if replace_from in top_dict.FullName:
                        top_dict.FullName = top_dict.FullName.replace(replace_from, replace_to)
                        print(f"Replaced in CFF FullName: {top_dict.FullName}")
                
                if hasattr(top_dict, 'FamilyName') and top_dict.FamilyName:
                    if replace_from in top_dict.FamilyName:
                        top_dict.FamilyName = top_dict.FamilyName.replace(replace_from, replace_to)
                        print(f"Replaced in CFF FamilyName: {top_dict.FamilyName}")
                
                if hasattr(top_dict, 'version') and top_dict.version:
                    if replace_from in top_dict.version:
                        top_dict.version = top_dict.version.replace(replace_from, replace_to)
                        print(f"Replaced in CFF version: {top_dict.version}")
                
                if hasattr(top_dict, 'Notice') and top_dict.Notice:
                    if replace_from in top_dict.Notice:
                        top_dict.Notice = top_dict.Notice.replace(replace_from, replace_to)
                        print(f"Replaced in CFF Notice: {top_dict.Notice}")
                
                if hasattr(top_dict, 'Copyright') and top_dict.Copyright:
                    if replace_from in top_dict.Copyright:
                        top_dict.Copyright = top_dict.Copyright.replace(replace_from, replace_to)
                        print(f"Replaced in CFF Copyright: {top_dict.Copyright}")
    
    # Save the modified font
    font.save(output_ttf)
    print(f"\nSaved modified font to: {output_ttf}")


def main():
    parser = argparse.ArgumentParser(
        description='Replace text in all metadata fields of a TTF font'
    )
    parser.add_argument('input_ttf', help='Input TTF file path')
    parser.add_argument('replace_from', help='Text to search for')
    parser.add_argument('replace_to', help='Text to replace with')
    parser.add_argument('output_ttf', help='Output TTF file path')
    
    args = parser.parse_args()
    
    replace_metadata(
        args.input_ttf,
        args.replace_from,
        args.replace_to,
        args.output_ttf
    )


if __name__ == '__main__':
    main()
