#!/usr/bin/env python3
"""
Remove monospace markings from a TTF font file.
Reverses the monospace flags set by merge_font.py.
"""

import argparse
from pathlib import Path
from fontTools.ttLib import TTFont


def unmono_font(input_ttf, output_ttf):
    """Remove monospace/fixed-pitch markings from a font."""
    
    print(f"Loading font: {input_ttf}")
    font = TTFont(input_ttf)
    
    # Update post table - remove fixed pitch marking
    if 'post' in font:
        print("Removing fixed-pitch marking from post table...")
        post_table = font['post']
        post_table.isFixedPitch = 0
    
    # Update OS/2 table - remove monospace marking
    if 'OS/2' in font:
        print("Removing monospace marking from OS/2 table...")
        os2 = font['OS/2']
        # Set to proportional (value 3) instead of monospace (value 9)
        os2.panose.bProportion = 3
    
    # Save the modified font
    print(f"Saving font to: {output_ttf}")
    font.save(output_ttf)
    print("Done!")


def main():
    parser = argparse.ArgumentParser(
        description='Remove monospace markings from a TTF font',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Example:
  %(prog)s input/monospaced.ttf output/proportional.ttf
        """
    )
    
    parser.add_argument(
        'input_ttf',
        type=str,
        help='Input TTF file with monospace markings'
    )
    
    parser.add_argument(
        'output_ttf',
        type=str,
        help='Output TTF file without monospace markings'
    )
    
    args = parser.parse_args()
    
    # Validate input file
    if not Path(args.input_ttf).exists():
        print(f"Error: Input file not found: {args.input_ttf}")
        return 1
    
    # Ensure output directory exists
    output_dir = Path(args.output_ttf).parent
    if output_dir != Path('.'):
        output_dir.mkdir(parents=True, exist_ok=True)
    
    unmono_font(args.input_ttf, args.output_ttf)
    return 0


if __name__ == '__main__':
    exit(main())
