#!/usr/bin/env python3

import argparse
from fontTools.ttLib import TTFont
from fontTools.pens.recordingPen import DecomposingRecordingPen
from fontTools.pens.ttGlyphPen import TTGlyphPen


def decompose_composite_glyphs(input_ttf, output_ttf):
    """
    Decompose all composite glyphs in a TrueType font.
    
    Args:
        input_ttf: Path to the input TTF file
        output_ttf: Path to the output TTF file
    """
    # Load the font
    font = TTFont(input_ttf)
    
    # Get the glyf table
    glyf_table = font['glyf']
    glyph_set = font.getGlyphSet()
    
    # Iterate through all glyphs
    for glyph_name in glyf_table.keys():
        glyph = glyf_table[glyph_name]
        
        # Check if it's a composite glyph
        if glyph.isComposite():
            # First, use DecomposingRecordingPen to decompose the components
            recording_pen = DecomposingRecordingPen(glyph_set)
            glyph_set[glyph_name].draw(recording_pen)
            
            # Create a new TTGlyphPen to create the decomposed glyph
            tt_pen = TTGlyphPen(glyph_set)
            
            # Replay the recorded (decomposed) drawing operations
            recording_pen.replay(tt_pen)
            
            # Replace the composite glyph with the decomposed version
            glyf_table[glyph_name] = tt_pen.glyph()
    
    # Save the modified font
    font.save(output_ttf)
    print(f"Decomposed composite glyphs and saved to {output_ttf}")


def main():
    parser = argparse.ArgumentParser(
        description='Decompose composite glyphs in a TrueType font'
    )
    parser.add_argument(
        'input_ttf',
        help='Path to the input TTF file'
    )
    parser.add_argument(
        'output_ttf',
        help='Path to the output TTF file'
    )
    
    args = parser.parse_args()
    
    decompose_composite_glyphs(args.input_ttf, args.output_ttf)


if __name__ == '__main__':
    main()
