#!/usr/bin/env python3

import argparse
from fontTools.ttLib import TTFont


def main():
    parser = argparse.ArgumentParser(
        description='Convert post table formatType to 3'
    )
    parser.add_argument('input_ttf', help='Input TTF file')
    parser.add_argument('output_ttf', help='Output TTF file')
    
    args = parser.parse_args()
    
    # Load the font
    font = TTFont(args.input_ttf)
    
    # Convert post table formatType to 3
    if 'post' in font:
        font['post'].formatType = 3.0
    
    # Save the font
    font.save(args.output_ttf)
    
    print(f"Converted post table to formatType 3: {args.output_ttf}")


if __name__ == '__main__':
    main()
