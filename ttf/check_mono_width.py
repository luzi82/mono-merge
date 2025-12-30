#!/usr/bin/env python3
"""
check_widths.py: Check if a font contains non-standard character widths
Identifies glyphs that don't advance by exactly 1 or 2 half-width units,
which would break monospace alignment in code editors and terminals.
"""

import argparse
import sys
from pathlib import Path
from collections import Counter
from fontTools.ttLib import TTFont


def get_font_metrics(font):
    """
    Determine the dominant half-width and full-width of the font.
    Returns (half_width, full_width)
    """
    hmtx = font['hmtx']
    cmap = font.getBestCmap()
    
    # Try to find standard chars
    half_width = None
    full_width = None
    
    # Space (0x20) or 'A' (0x41) for half-width
    for cp in [0x20, 0x41]:
        if cp in cmap:
            half_width = hmtx[cmap[cp]][0]
            break
            
    # 'One' (0x4E00) or Ideographic Space (0x3000) for full-width
    for cp in [0x4E00, 0x3000]:
        if cp in cmap:
            full_width = hmtx[cmap[cp]][0]
            break
            
    # Fallback to statistics if needed
    if half_width is None or full_width is None:
        widths = [hmtx[name][0] for name in cmap.values()]
        if not widths:
            return 0, 0
        common = Counter(widths).most_common(2)
        sorted_widths = sorted([c[0] for c in common])
        
        if len(sorted_widths) == 1:
            # Only one width found
            w = sorted_widths[0]
            # Guess based on UPM
            upm = font['head'].unitsPerEm
            if abs(w - upm) < abs(w - upm/2):
                full_width = w
                half_width = w // 2
            else:
                half_width = w
                full_width = w * 2
        else:
            if half_width is None: half_width = sorted_widths[0]
            if full_width is None: full_width = sorted_widths[-1]
            
    return half_width, full_width


def check_font_widths(font_path, ttc_index=0, tolerance=0):
    """
    Check if all glyphs advance by exactly 1 or 2 half-width units.
    Characters with other widths will misalign text in monospace contexts.
    
    Args:
        font_path: Path to the font file (TTF/TTC)
        ttc_index: Font index if TTC file
        tolerance: Allowed deviation from standard widths (default: 0)
    
    Returns:
        dict with 'valid' (bool) and 'issues' (list of problematic glyphs)
    """
    # Load font
    font = TTFont(font_path, fontNumber=ttc_index)
    
    # Get standard widths
    half_width, full_width = get_font_metrics(font)
    
    print(f"Font: {font_path}")
    if font_path.suffix.lower() == '.ttc':
        print(f"TTC Index: {ttc_index}")
    print(f"Standard Half Width: {half_width}")
    print(f"Standard Full Width: {full_width}")
    print(f"Tolerance: ±{tolerance}")
    print()
    
    # Check all glyphs
    hmtx = font['hmtx']
    cmap = font.getBestCmap()
    
    issues = []
    zero_width_count = 0
    
    for codepoint, glyph_name in cmap.items():
        width = hmtx[glyph_name][0]
        
        # Skip zero-width glyphs (combining marks, etc.)
        if width == 0:
            zero_width_count += 1
            continue
        
        # Check if width advances by exactly 1 or 2 half-width units (within tolerance)
        # Non-standard widths break monospace alignment
        is_half = abs(width - half_width) <= tolerance
        is_full = abs(width - full_width) <= tolerance
        
        if not (is_half or is_full):
            char = chr(codepoint)
            char_display = repr(char)[1:-1]  # Remove quotes
            issues.append({
                'codepoint': codepoint,
                'char': char_display,
                'glyph_name': glyph_name,
                'width': width,
                'deviation_from_half': width - half_width,
                'deviation_from_full': width - full_width
            })
    
    # Print results
    if issues:
        print(f"⚠️  Found {len(issues)} glyphs with non-standard widths:")
        print(f"    (These will break monospace alignment when displayed)")
        print()
        for issue in issues:
            print(f"  U+{issue['codepoint']:04X} '{issue['char']}' ({issue['glyph_name']})")
            print(f"    Width: {issue['width']}")
            print(f"    Deviation from half-width: {issue['deviation_from_half']:+d}")
            print(f"    Deviation from full-width: {issue['deviation_from_full']:+d}")
            print()
    else:
        print(f"✓ All {len(cmap)} character(s) have standard widths")
        if zero_width_count > 0:
            print(f"  ({zero_width_count} zero-width glyphs ignored)")
    
    return {
        'valid': len(issues) == 0,
        'issues': issues,
        'half_width': half_width,
        'full_width': full_width,
        'total_chars': len(cmap),
        'zero_width_count': zero_width_count
    }


def main():
    parser = argparse.ArgumentParser(
        description='Check if font characters advance by exactly 1 or 2 half-width units (for proper monospace alignment)',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s output.ttf
  %(prog)s output.ttc --ttc-index 0
  %(prog)s output.ttf --tolerance 5
        """
    )
    
    parser.add_argument('font', type=Path,
                        help='Path to the font file (TTF/TTC)')
    parser.add_argument('--ttc-index', type=int, default=0,
                        help='Font index for TTC files (default: 0)')
    parser.add_argument('--tolerance', type=int, default=0,
                        help='Allowed deviation from standard widths (default: 0)')
    
    args = parser.parse_args()
    
    # Validate input
    if not args.font.exists():
        print(f"Error: Font file not found: {args.font}", file=sys.stderr)
        return 1
    
    # Check widths
    result = check_font_widths(args.font, args.ttc_index, args.tolerance)
    
    # Return exit code
    return 0 if result['valid'] else 1


if __name__ == '__main__':
    sys.exit(main())
