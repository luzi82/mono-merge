#!/usr/bin/env python3
import argparse
import sys
from fontTools.ttLib import TTFont

def inspect_font(path, index=0, chars="測試文字"):
    print(f"=== Inspecting {path} (index {index}) ===")
    try:
        font = TTFont(path, fontNumber=index)
    except Exception as e:
        print(f"Error loading font: {e}")
        return

    # 1. Basic Info & Glyph Order
    glyph_order = font.getGlyphOrder()
    print(f"\n[Glyph Order]")
    print(f"  Total glyphs: {len(glyph_order)}")
    print(f"  First 10 glyphs: {glyph_order[:10]}")
    
    generic_count = sum(1 for name in glyph_order if name.startswith('glyph'))
    print(f"  Glyphs starting with 'glyph': {generic_count}")

    # 2. Cmap Tables
    print(f"\n[Cmap Tables]")
    if 'cmap' in font:
        for table in font['cmap'].tables:
            print(f"  Platform: {table.platformID}, Encoding: {table.platEncID}, Format: {table.format}, Unicode: {table.isUnicode()}")
    else:
        print("  No cmap table found")

    # 3. Character Mapping & Glyph Existence
    print(f"\n[Character Mapping & Glyph Existence]")
    cmap = font.getBestCmap()
    if cmap:
        print(f"  Best cmap size: {len(cmap)}")
        
        glyf = font.get('glyf')
        if glyf is None:
             print("  (No 'glyf' table found)")

        for char in chars:
            cp = ord(char)
            if cp in cmap:
                gname = cmap[cp]
                status = []
                
                if gname in glyph_order:
                    status.append("in glyphOrder")
                else:
                    status.append("NOT in glyphOrder")
                
                if glyf:
                    if gname in glyf:
                        status.append("in glyf table")
                    else:
                        status.append("NOT in glyf table")
                
                print(f"  '{char}' (U+{cp:04X}) -> {gname} ({', '.join(status)})")
            else:
                print(f"  '{char}' (U+{cp:04X}) -> NOT FOUND in cmap")
    else:
        print("  No suitable cmap found")

def main():
    parser = argparse.ArgumentParser(description="Inspect font details for debugging.")
    parser.add_argument("path", help="Path to the font file")
    parser.add_argument("-i", "--index", type=int, default=0, help="Font index (default: 0)")
    parser.add_argument("-c", "--chars", default="測試文字", help="Characters to check (default: 測試文字)")
    
    args = parser.parse_args()
    inspect_font(args.path, args.index, args.chars)

if __name__ == "__main__":
    main()
