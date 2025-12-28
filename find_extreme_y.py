#!/usr/bin/env python3
"""
Find characters with extreme y-values in a font.

This tool analyzes glyph bounding boxes to identify characters with unusually
high or low y-coordinates, which may indicate positioning issues or outliers.
"""

import argparse
import sys
from pathlib import Path
from fontTools import ttLib


def is_ascii_char(codepoint):
    """Check if a codepoint is an ASCII character."""
    # ASCII range: 0x0000-0x007F (0-127)
    return 0x0000 <= codepoint <= 0x007F


def is_latin_char(codepoint):
    """Check if a codepoint is a Latin character."""
    # Basic Latin (0x0000-0x007F)
    # Latin-1 Supplement (0x0080-0x00FF)
    # Latin Extended-A (0x0100-0x017F)
    # Latin Extended-B (0x0180-0x024F)
    # Latin Extended Additional (0x1E00-0x1EFF)
    return (
        (0x0000 <= codepoint <= 0x007F) or
        (0x0080 <= codepoint <= 0x00FF) or
        (0x0100 <= codepoint <= 0x017F) or
        (0x0180 <= codepoint <= 0x024F) or
        (0x1E00 <= codepoint <= 0x1EFF)
    )


def is_cjk_char(codepoint):
    """Check if a codepoint is a CJK character."""
    # CJK Unified Ideographs (0x4E00-0x9FFF)
    # CJK Unified Ideographs Extension A (0x3400-0x4DBF)
    # CJK Unified Ideographs Extension B (0x20000-0x2A6DF)
    # CJK Unified Ideographs Extension C (0x2A700-0x2B73F)
    # CJK Unified Ideographs Extension D (0x2B740-0x2B81F)
    # CJK Unified Ideographs Extension E (0x2B820-0x2CEAF)
    # CJK Unified Ideographs Extension F (0x2CEB0-0x2EBEF)
    # CJK Compatibility Ideographs (0xF900-0xFAFF)
    # CJK Compatibility Ideographs Supplement (0x2F800-0x2FA1F)
    # Hiragana (0x3040-0x309F)
    # Katakana (0x30A0-0x30FF)
    # Hangul Syllables (0xAC00-0xD7AF)
    return (
        (0x4E00 <= codepoint <= 0x9FFF) or
        (0x3400 <= codepoint <= 0x4DBF) or
        (0x20000 <= codepoint <= 0x2A6DF) or
        (0x2A700 <= codepoint <= 0x2B73F) or
        (0x2B740 <= codepoint <= 0x2B81F) or
        (0x2B820 <= codepoint <= 0x2CEAF) or
        (0x2CEB0 <= codepoint <= 0x2EBEF) or
        (0xF900 <= codepoint <= 0xFAFF) or
        (0x2F800 <= codepoint <= 0x2FA1F) or
        (0x3040 <= codepoint <= 0x309F) or
        (0x30A0 <= codepoint <= 0x30FF) or
        (0xAC00 <= codepoint <= 0xD7AF)
    )


def analyze_font_y_values(font_path, ttc_index=0, threshold_percentile=95, char_filter=None):
    """
    Analyze font glyphs for extreme y-values.
    
    Args:
        font_path: Path to the font file (TTF, OTF, TTC)
        ttc_index: Index for TTC files (default: 0)
        threshold_percentile: Percentile to consider as extreme (default: 95)        char_filter: Filter to apply ('latin', 'cjk', or None for all)    
    Returns:
        Dictionary with analysis results
    """
    # Load the font
    font = ttLib.TTFont(font_path, fontNumber=ttc_index)
    
    # Get character map
    cmap = font.getBestCmap()
    if not cmap:
        print("Error: No character map found in font", file=sys.stderr)
        return None
    
    # Determine if font is TrueType (glyf) or OpenType/CFF (CFF )
    glyf = font.get('glyf')
    cff = font.get('CFF ')
    
    if not glyf and not cff:
        print("Error: Font has neither 'glyf' (TrueType) nor 'CFF ' (OpenType) table", file=sys.stderr)
        return None
    
    # For CFF fonts, we need to use the CFF table
    if cff:
        cff_dict = cff.cff[0]
        char_strings = cff_dict.CharStrings
    
    # Collect y-values for all glyphs
    glyph_data = []
    
    for codepoint, glyph_name in cmap.items():
        # Apply character filter
        if char_filter == 'ascii' and not is_ascii_char(codepoint):
            continue
        elif char_filter == 'latin' and not is_latin_char(codepoint):
            continue
        elif char_filter == 'cjk' and not is_cjk_char(codepoint):
            continue
        
        try:
            xMin, yMin, xMax, yMax = None, None, None, None
            
            if glyf and glyph_name in glyf:
                # TrueType font
                glyph = glyf[glyph_name]
                
                # Check if glyph has bounding box attributes
                if hasattr(glyph, 'xMin') and hasattr(glyph, 'yMin'):
                    xMin = glyph.xMin
                    yMin = glyph.yMin
                    xMax = glyph.xMax
                    yMax = glyph.yMax
            
            elif cff and glyph_name in char_strings:
                # OpenType/CFF font
                charstring = char_strings[glyph_name]
                # Get bounding box by calculating bounds
                bounds = charstring.calcBounds(char_strings)
                if bounds:
                    xMin, yMin, xMax, yMax = bounds
            
            if xMin is not None and yMin is not None:
                char = chr(codepoint)
                
                glyph_data.append({
                    'codepoint': codepoint,
                    'char': char,
                    'glyph_name': glyph_name,
                    'yMin': yMin,
                    'yMax': yMax,
                    'y_range': yMax - yMin
                })
        except Exception as e:
            # Skip glyphs that can't be processed
            pass
    
    if not glyph_data:
        print("Error: No valid glyph data found", file=sys.stderr)
        return None
    
    # Calculate statistics
    y_mins = [g['yMin'] for g in glyph_data]
    y_maxs = [g['yMax'] for g in glyph_data]
    
    y_mins_sorted = sorted(y_mins)
    y_maxs_sorted = sorted(y_maxs)
    
    # Calculate percentile thresholds
    low_index = int(len(y_mins_sorted) * (100 - threshold_percentile) / 100)
    high_index = int(len(y_maxs_sorted) * threshold_percentile / 100)
    
    low_threshold = y_mins_sorted[low_index] if low_index < len(y_mins_sorted) else y_mins_sorted[0]
    high_threshold = y_maxs_sorted[high_index] if high_index < len(y_maxs_sorted) else y_maxs_sorted[-1]
    
    # Find outliers
    extreme_low = [g for g in glyph_data if g['yMin'] < low_threshold]
    extreme_high = [g for g in glyph_data if g['yMax'] > high_threshold]
    
    # Sort by extremity
    extreme_low.sort(key=lambda g: g['yMin'])
    extreme_high.sort(key=lambda g: g['yMax'], reverse=True)
    
    return {
        'total_glyphs': len(glyph_data),
        'yMin_range': (min(y_mins), max(y_mins)),
        'yMax_range': (min(y_maxs), max(y_maxs)),
        'low_threshold': low_threshold,
        'high_threshold': high_threshold,
        'extreme_low': extreme_low,
        'extreme_high': extreme_high
    }


def print_results(results, show_all=False, limit=20):
    """Print analysis results."""
    if not results:
        return
    
    print(f"Font Analysis: {results['total_glyphs']} glyphs analyzed")
    print(f"yMin range: {results['yMin_range'][0]:.1f} to {results['yMin_range'][1]:.1f}")
    print(f"yMax range: {results['yMax_range'][0]:.1f} to {results['yMax_range'][1]:.1f}")
    print()
    
    print(f"Low threshold (yMin < {results['low_threshold']:.1f}):")
    print("-" * 80)
    
    extreme_low = results['extreme_low'] if show_all else results['extreme_low'][:limit]
    if extreme_low:
        print(f"{'Char':<8} {'U+Code':<10} {'Glyph Name':<30} {'yMin':<10} {'yMax':<10}")
        print("-" * 80)
        for g in extreme_low:
            char_repr = g['char'] if g['char'].isprintable() else '·'
            print(f"{char_repr:<8} U+{g['codepoint']:04X}    {g['glyph_name']:<30} "
                  f"{g['yMin']:<10.1f} {g['yMax']:<10.1f}")
    else:
        print("No characters found below threshold")
    
    print()
    print(f"High threshold (yMax > {results['high_threshold']:.1f}):")
    print("-" * 80)
    
    extreme_high = results['extreme_high'] if show_all else results['extreme_high'][:limit]
    if extreme_high:
        print(f"{'Char':<8} {'U+Code':<10} {'Glyph Name':<30} {'yMin':<10} {'yMax':<10}")
        print("-" * 80)
        for g in extreme_high:
            char_repr = g['char'] if g['char'].isprintable() else '·'
            print(f"{char_repr:<8} U+{g['codepoint']:04X}    {g['glyph_name']:<30} "
                  f"{g['yMin']:<10.1f} {g['yMax']:<10.1f}")
    else:
        print("No characters found above threshold")
    
    if not show_all and (len(results['extreme_low']) > limit or len(results['extreme_high']) > limit):
        print()
        print(f"(Showing top {limit} results. Use --all to show all outliers)")


def main():
    parser = argparse.ArgumentParser(
        description='Find characters with extreme y-values in a font',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s font.ttf
  %(prog)s font.ttc --index 1
  %(prog)s font.ttf --percentile 99
  %(prog)s font.ttf --all
        """
    )
    
    parser.add_argument('font', type=str, help='Path to font file (TTF, OTF, TTC)')
    parser.add_argument('--index', type=int, default=0,
                        help='Font index for TTC files (default: 0)')
    parser.add_argument('--percentile', type=float, default=95.0,
                        help='Percentile threshold for extremes (default: 95.0)')
    parser.add_argument('--limit', type=int, default=20,
                        help='Maximum number of outliers to show per category (default: 20)')
    parser.add_argument('--all', action='store_true',
                        help='Show all outliers (ignore --limit)')
    parser.add_argument('--ascii', action='store_true',
                        help='Only analyze ASCII characters (0x00-0x7F)')
    parser.add_argument('--latin', action='store_true',
                        help='Only analyze Latin characters')
    parser.add_argument('--cjk', action='store_true',
                        help='Only analyze CJK characters')
    
    args = parser.parse_args()
    
    # Check if font file exists
    font_path = Path(args.font)
    if not font_path.exists():
        print(f"Error: Font file not found: {args.font}", file=sys.stderr)
        sys.exit(1)
    
    # Validate percentile
    if not 50.0 <= args.percentile <= 100.0:
        print("Error: Percentile must be between 50 and 100", file=sys.stderr)
        sys.exit(1)
    
    # Validate filter flags (mutually exclusive)
    filter_count = sum([args.ascii, args.latin, args.cjk])
    if filter_count > 1:
        print("Error: Cannot use multiple character filter flags (--ascii, --latin, --cjk)", file=sys.stderr)
        sys.exit(1)
    
    # Determine character filter
    char_filter = None
    if args.ascii:
        char_filter = 'ascii'
    elif args.latin:
        char_filter = 'latin'
    elif args.cjk:
        char_filter = 'cjk'
    
    # Analyze font
    try:
        results = analyze_font_y_values(args.font, args.index, args.percentile, char_filter)
        if results:
            print_results(results, args.all, args.limit)
    except Exception as e:
        print(f"Error analyzing font: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()
