#!/usr/bin/env python3

import argparse
from fontTools.ttLib import TTFont


def main():
    parser = argparse.ArgumentParser(
        description='Remove specified tables from a TTF file'
    )
    parser.add_argument('input_ttf', help='Input TTF file')
    parser.add_argument('table_names', help='Comma-separated list of table names to remove (e.g., GPOS,GSUB)')
    parser.add_argument('output_ttf', help='Output TTF file')
    
    args = parser.parse_args()
    
    # Load the font
    font = TTFont(args.input_ttf)
    
    # Parse table names
    table_list = [name.strip() for name in args.table_names.split(',')]
    
    # Remove each specified table if it exists
    for table_name in table_list:
        if table_name in font:
            del font[table_name]
            print(f"Removed {table_name} table")
        else:
            print(f"{table_name} table not found")
    
    # Save the modified font
    font.save(args.output_ttf)
    print(f"Saved to {args.output_ttf}")


if __name__ == '__main__':
    main()
