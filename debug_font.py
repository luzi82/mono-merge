#!/usr/bin/env python3
import argparse
import sys
from fontTools.ttLib import TTFont
from fontTools.pens.ttGlyphPen import TTGlyphPen
from fontTools.pens.transformPen import TransformPen

def inspect_font(path, index=0, chars="測試文字", scale=1.0):
    print(f"=== Inspecting {path} (index {index}) ===")
    try:
        font = TTFont(path, fontNumber=index)
    except Exception as e:
        print(f"Error loading font: {e}")
        return

    # 0. Monospace/Fixed-Pitch Properties
    print(f"\n[Monospace/Fixed-Pitch Properties]")
    if 'post' in font:
        print(f"  post.isFixedPitch: {font['post'].isFixedPitch}")
    else:
        print("  No 'post' table found")
    
    if 'OS/2' in font:
        os2 = font['OS/2']
        print(f"  OS/2.panose.bProportion: {os2.panose.bProportion} (9 = monospace)")
        print(f"  OS/2.panose.bFamilyType: {os2.panose.bFamilyType}")
        print(f"  OS/2.xAvgCharWidth: {os2.xAvgCharWidth}")
        print(f"  OS/2.sFamilyClass: {os2.sFamilyClass}")
    else:
        print("  No 'OS/2' table found")

    # 1. Head Info (UPM)
    if 'head' in font:
        print(f"\n[Head Table]")
        print(f"  UnitsPerEm: {font['head'].unitsPerEm}")
        print(f"  xMin: {font['head'].xMin}, yMin: {font['head'].yMin}")
        print(f"  xMax: {font['head'].xMax}, yMax: {font['head'].yMax}")
        print(f"  macStyle: {font['head'].macStyle}")

    # 2. Basic Info & Glyph Order
    glyph_order = font.getGlyphOrder()
    print(f"\n[Glyph Order]")
    print(f"  Total glyphs: {len(glyph_order)}")
    print(f"  First 10 glyphs: {glyph_order[:10]}")
    
    generic_count = sum(1 for name in glyph_order if name.startswith('glyph'))
    print(f"  Glyphs starting with 'glyph': {generic_count}")

    # 3. Cmap Tables
    print(f"\n[Cmap Tables]")
    if 'cmap' in font:
        for table in font['cmap'].tables:
            print(f"  Platform: {table.platformID}, Encoding: {table.platEncID}, Format: {table.format}, Unicode: {table.isUnicode()}")
    else:
        print("  No cmap table found")

    # 4. Character Mapping & Glyph Existence
    print(f"\n[Character Mapping & Glyph Existence]")
    cmap = font.getBestCmap()
    if cmap:
        print(f"  Best cmap size: {len(cmap)}")
        
        glyf = font.get('glyf')
        hmtx = font.get('hmtx')
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
                
                metrics = ""
                if hmtx and hasattr(hmtx, 'metrics') and gname in hmtx.metrics:
                    width, lsb = hmtx.metrics[gname]
                    metrics = f"Width: {width}, LSB: {lsb}"
                
                bbox = ""
                comp_info = ""
                if glyf and gname in glyf:
                    status.append("in glyf table")
                    g = glyf[gname]
                    comp_info = "Composite" if g.isComposite() else "Simple"
                    if hasattr(g, 'xMin'):
                        bbox = f"BBox: ({g.xMin}, {g.yMin}) - ({g.xMax}, {g.yMax})"
                else:
                    status.append("NOT in glyph table")
                
                print(f"  '{char}' (U+{cp:04X}) -> {gname} ({', '.join(status)}) {metrics} {bbox} [{comp_info}]")
                
                if scale != 1.0 and glyf and gname in glyf:
                    try:
                        g = glyf[gname]
                        pen = TTGlyphPen(glyf)
                        tpen = TransformPen(pen, (scale, 0, 0, scale, 0, 0))
                        g.draw(tpen, glyf)
                        new_g = pen.glyph()
                        new_g.recalcBounds(glyf)
                        
                        new_bbox = f"Scaled BBox: ({new_g.xMin}, {new_g.yMin}) - ({new_g.xMax}, {new_g.yMax})"
                        print(f"    -> Scaled ({scale}x): {new_bbox}")
                    except Exception as e:
                        print(f"    -> Scaling failed: {e}")
            else:
                print(f"  '{char}' (U+{cp:04X}) -> NOT FOUND in cmap")
    else:
        print("  No suitable cmap found")

def main():
    parser = argparse.ArgumentParser(description="Inspect font details for debugging.")
    parser.add_argument("path", help="Path to the font file")
    parser.add_argument("-i", "--index", type=int, default=0, help="Font index (default: 0)")
    parser.add_argument("-c", "--chars", default="A測試文字", help="Characters to check (default: A測試文字)")
    parser.add_argument("-s", "--scale", type=float, default=1.0, help="Scale factor to simulate (default: 1.0)")
    
    args = parser.parse_args()
    inspect_font(args.path, args.index, args.chars, args.scale)

if __name__ == "__main__":
    main()
