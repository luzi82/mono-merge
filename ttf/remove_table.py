#!/usr/bin/env python3

import argparse
from fontTools.ttLib import TTFont


def remove_tables(input_ttf, output_ttf):
    """
    Remove GPOS and GSUB tables from a TTF/OTF font file.
    
    Args:
        input_ttf: Path to the input font file
        output_ttf: Path to the output font file
    """
    # Load the font
    font = TTFont(input_ttf)
    
    # List of tables to remove
    tables_to_remove = ['GPOS', 'GSUB']
    
    # Remove tables if they exist
    for table_name in tables_to_remove:
        if table_name in font:
            del font[table_name]
            print(f"Removed {table_name} table")
        else:
            print(f"{table_name} table not found in font")
    
    # Save the modified font
    font.save(output_ttf)
    print(f"Saved font to {output_ttf}")


def main():
    parser = argparse.ArgumentParser(
        description='Remove GPOS and GSUB tables from a TTF/OTF font file'
    )
    parser.add_argument(
        'input_ttf',
        help='Path to the input TTF/OTF file'
    )
    parser.add_argument(
        'output_ttf',
        help='Path to the output TTF/OTF file'
    )
    
    args = parser.parse_args()
    
    remove_tables(args.input_ttf, args.output_ttf)


if __name__ == '__main__':
    main()
