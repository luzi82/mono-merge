#!/usr/bin/env python3

import argparse
from fontTools.ttLib import TTFont


def main():
    parser = argparse.ArgumentParser(
        description='Set font metadata in a TTF file'
    )
    parser.add_argument(
        'input_ttf',
        help='Input TTF file path'
    )
    parser.add_argument(
        '--units-per-em',
        type=int,
        help='Update head.unitsPerEm value'
    )
    parser.add_argument(
        'output_ttf',
        help='Output TTF file path'
    )
    
    args = parser.parse_args()
    
    # Load the font
    font = TTFont(args.input_ttf)
    
    # Update units_per_em if provided
    if args.units_per_em is not None:
        if 'head' not in font:
            raise ValueError("Font does not contain a 'head' table")
        font['head'].unitsPerEm = args.units_per_em
        print(f"Updated unitsPerEm to {args.units_per_em}")
    
    # Save the modified font
    font.save(args.output_ttf)
    print(f"Saved font to {args.output_ttf}")


if __name__ == '__main__':
    main()
