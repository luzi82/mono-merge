#!/usr/bin/env python3
"""
Font Preview Tool for Debugging
Renders test text with a specified font and generates debug information
"""

import argparse
import sys
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
import yaml
from fontTools.ttLib import TTFont


def get_font_info(font_path, font_index=0):
    """Extract font information for debugging"""
    try:
        ttfont = TTFont(font_path, fontNumber=font_index)
        info = {
            'file_path': str(font_path),
            'tables': list(ttfont.keys()),
        }
        
        # Get font names
        if 'name' in ttfont:
            name_table = ttfont['name']
            info['names'] = {}
            for record in name_table.names:
                try:
                    name_id = record.nameID
                    name_value = record.toUnicode()
                    if name_id not in info['names']:
                        info['names'][name_id] = []
                    info['names'][name_id].append({
                        'platform': record.platformID,
                        'encoding': record.platEncID,
                        'language': record.langID,
                        'value': name_value
                    })
                except:
                    pass
        
        # Get character map info
        if 'cmap' in ttfont:
            cmap = ttfont.getBestCmap()
            if cmap:
                info['num_glyphs_mapped'] = len(cmap)
                info['codepoint_range'] = {
                    'min': min(cmap.keys()),
                    'max': max(cmap.keys()),
                    'min_hex': f"U+{min(cmap.keys()):04X}",
                    'max_hex': f"U+{max(cmap.keys()):04X}"
                }
        
        # Get metrics
        if 'head' in ttfont:
            head = ttfont['head']
            info['units_per_em'] = head.unitsPerEm
        
        if 'hhea' in ttfont:
            hhea = ttfont['hhea']
            info['ascent'] = hhea.ascent
            info['descent'] = hhea.descent
            info['line_gap'] = hhea.lineGap
        
        # Get OS/2 metrics if available
        if 'OS/2' in ttfont:
            os2 = ttfont['OS/2']
            info['os2_metrics'] = {
                'typo_ascender': os2.sTypoAscender,
                'typo_descender': os2.sTypoDescender,
                'typo_line_gap': os2.sTypoLineGap,
                'win_ascent': os2.usWinAscent,
                'win_descent': os2.usWinDescent,
            }
        
        ttfont.close()
        return info
    except Exception as e:
        return {'error': str(e)}


def render_text_preview(font_path, text, output_prefix, font_size=48, font_index=0, debug=False):
    """Render text using the specified font and save as PNG"""
    try:
        # Create image with white background
        img_width = 1200
        img_height = 300
        background_color = (255, 255, 255)
        text_color = (0, 0, 0)
        
        image = Image.new('RGB', (img_width, img_height), background_color)
        draw = ImageDraw.Draw(image)
        
        # Load font
        try:
            font = ImageFont.truetype(str(font_path), font_size, index=font_index)
        except Exception as e:
            # If font loading fails, include error in debug info
            return None, {'font_load_error': str(e)}
        
        # Calculate text position (centered)
        # Get bounding box of text
        bbox = draw.textbbox((0, 0), text, font=font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]
        
        x = (img_width - text_width) // 2
        y = (img_height - text_height) // 2
        
        # Draw text
        draw.text((x, y), text, fill=text_color, font=font)
        
        if debug:
            # Get font metrics
            ascent, descent = font.getmetrics()
            
            # Calculate lines based on anchor 'la' (Left, Ascender) which is default for draw.text?
            # Actually, let's check the bbox relative to (x,y) to be sure where things are.
            real_bbox = draw.textbbox((x, y), text, font=font)
            
            # Draw bounding box (Orange)
            draw.rectangle(real_bbox, outline=(255, 165, 0), width=1)
            
            # Assuming default anchor 'la' (Left, Ascender)
            # (x, y) is the top-left of the em-square (ascender line)
            # But wait, if we used (x,y) calculated from bbox to center it, 
            # we need to know what (x,y) represents.
            # draw.text((x,y), ...) draws at (x,y).
            # If default anchor is 'la', then y is the ascender line.
            
            baseline_y = y + ascent
            ascent_y = y
            descent_y = y + ascent + descent
            
            # Draw Baseline (Blue)
            draw.line([(0, baseline_y), (img_width, baseline_y)], fill=(0, 0, 255), width=1)
            
            # Draw Ascender (Green)
            draw.line([(0, ascent_y), (img_width, ascent_y)], fill=(0, 255, 0), width=1)
            
            # Draw Descender (Red)
            draw.line([(0, descent_y), (img_width, descent_y)], fill=(255, 0, 0), width=1)
            
            # Draw per-character vertical lines and boxes
            curr_x = x
            for char in text:
                # Draw vertical line at start of char (Cyan)
                draw.line([(curr_x, 0), (curr_x, img_height)], fill=(0, 255, 255), width=1)
                
                # Get char width
                char_width = font.getlength(char)
                
                # Draw char bbox (Light Gray)
                char_bbox = draw.textbbox((curr_x, y), char, font=font)
                draw.rectangle(char_bbox, outline=(200, 200, 200), width=1)
                
                curr_x += char_width
            
            # Draw final vertical line
            draw.line([(curr_x, 0), (curr_x, img_height)], fill=(0, 255, 255), width=1)

        # Save image
        output_png = f"{output_prefix}.png"
        image.save(output_png)
        
        # Prepare render info
        render_info = {
            'output_image': output_png,
            'image_size': {'width': img_width, 'height': img_height},
            'font_size': font_size,
            'font_index': font_index,
            'text': text,
            'text_length': len(text),
            'text_position': {'x': x, 'y': y},
            'text_bounding_box': {
                'left': bbox[0],
                'top': bbox[1],
                'right': bbox[2],
                'bottom': bbox[3],
                'width': text_width,
                'height': text_height
            }
        }
        
        return output_png, render_info
        
    except Exception as e:
        return None, {'render_error': str(e)}


def main():
    """Main function"""
    parser = argparse.ArgumentParser(
        description='Font Preview Tool - Render text with a font and generate debug information'
    )
    parser.add_argument(
        'font_file',
        type=str,
        help='Path to the font file (TTF, OTF, TTC, etc.)'
    )
    parser.add_argument(
        'test_text',
        type=str,
        help='Text to render'
    )
    parser.add_argument(
        'output_prefix',
        type=str,
        help='Output file prefix (will generate prefix.png and prefix.yaml)'
    )
    parser.add_argument(
        '--font-size',
        type=int,
        default=48,
        help='Font size for rendering (default: 48)'
    )
    parser.add_argument(
        '--font-index',
        type=int,
        default=0,
        help='Font index for TTC files (default: 0)'
    )
    parser.add_argument(
        '--debug',
        action='store_true',
        help='Enable debug output (bounding boxes, lines)'
    )
    
    args = parser.parse_args()
    
    # Validate font file exists
    font_path = Path(args.font_file)
    if not font_path.exists():
        print(f"Error: Font file not found: {args.font_file}", file=sys.stderr)
        sys.exit(1)
    
    print(f"Generating font preview")
    print(f"Font file: {args.font_file}")
    print(f"Font index: {args.font_index}")
    print(f"Test text: {args.test_text}")
    print(f"Output prefix: {args.output_prefix}")
    
    # Get font information
    print("\nExtracting font information...")
    font_info = get_font_info(font_path, args.font_index)
    
    # Render text preview
    print("Rendering text preview...")
    output_png, render_info = render_text_preview(
        font_path,
        args.test_text,
        args.output_prefix,
        args.font_size,
        args.font_index,
        debug=args.debug
    )
    
    # Prepare debug YAML
    debug_info = {
        'font_file': str(font_path.absolute()),
        'font_index': args.font_index,
        'test_text': args.test_text,
        'font_info': font_info,
        'render_info': render_info
    }
    
    # Save debug YAML
    output_yaml = f"{args.output_prefix}.yaml"
    with open(output_yaml, 'w', encoding='utf-8') as f:
        yaml.dump(debug_info, f, default_flow_style=False, allow_unicode=True, sort_keys=False)
    
    print(f"\n✓ Preview image saved: {output_png}")
    print(f"✓ Debug info saved: {output_yaml}")
    
    if output_png is None:
        print("\n⚠ Warning: Image rendering failed. Check debug YAML for details.", file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()
